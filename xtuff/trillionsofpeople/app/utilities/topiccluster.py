import distance
import numpy as np
from sklearn.cluster import AffinityPropagation

input = "Ignorance, Education, Pride, Luxury, Inconsideration, Disappointment and Resignation, Murmuring, Censoriousness, Bounds of Charity, Frugality or Bounty, Discipline, Industry, Temperance, Apparel, Right Marriage, Avarice, Friendship, Qualities of a Friend, Caution and Conduct, Reparation, Rules of Conversation, Eloquence, Temper, Truth, Justice, Secrecy, Complacency, Shifts, Interest, Inquiry, Right-timing, Knowledge, Wit, Obedience to Parents, Bearing, Promising, Fidelity, Master, Servant, Jealousy, Posterity, A Country Life, Art and Project, Industry, Temporal Happiness, Respect, Hazard, Detraction, Moderation, Trick, Passion, Personal Cautions, Ballance, Popularity, Privacy, Government, A Private Life, A Publick Life, Qualifications, Capacity, Clean Hands, Dispatch, Patience, Impartiality, Indifferency, Neutrality, A Party, Ostentation, Compleat Virtue, Religion, The Introduction to the Reader, The Right Moralist, The World’s Able Man, The Wise Man, Of the Government of Thoughts, Of Envy, Of Man’s Life, Of Ambition, Of Praise or Applause, Of Conduct in Speech, Union of Friends, Of Being Easy in Living, Of Man’s Inconsiderateness and Partiality, Of the Rule of Judging, Of Formality, Of the Mean Notion we Have of God, Of the Benefit of Justice, Of Jealousy, Of State, Of a Good Servant, Of an Immediate Pursuit of the World, Of the Interest of the Publick in our Estates, The Vain Man, The Conformist, The Obligations of Great Men to Almighty God, Of Refining upon Other Men’s Actions or Interests, Of Charity"
words = input.split(",") #Replace this line
words = np.asarray(words) #So that indexing with a list will work
lev_similarity = -1*np.array([[distance.levenshtein(w1,w2) for w1 in words] for w2 in words])

affprop = AffinityPropagation(affinity="precomputed", damping=0.5)
affprop.fit(lev_similarity)
for cluster_id in np.unique(affprop.labels_):
    exemplar = words[affprop.cluster_centers_indices_[cluster_id]]
    cluster = np.unique(words[np.nonzero(affprop.labels_==cluster_id)])
    cluster_str = ", ".join(cluster)
    print(" - *%s:* %s" % (exemplar, cluster_str))
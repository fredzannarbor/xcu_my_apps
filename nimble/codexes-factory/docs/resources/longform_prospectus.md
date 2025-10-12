
The immersive deep reading of high-quality books must rank among the most beneficial and broadly distributed technologies ever invented (see inter alia McLuhan, 1962; McDermott, 2006; Boorstin, 1992; UNESCO 2019). Yet this vital experience remains tightly constrained by scarcity: of classics, of representation, of accessibility, of sustainability, of time. It’s time to flip the script to a world of abundance.

A world where the dominant dopamine drip is not the addictive rage spiral of social media but the transformative insight and empathy of great books. A world where every culture and language can be represented in curricula with equal ease. A world where every author has equally powerful co-creators: new and globally available Muses. A world where every reader has an infinite bookshelf. A world where there are a thousand new Agatha Christies. A world where a helpful AI Muse saves George R.R. Martin from his tendency to be easily distracted. A world where our office learnings are instantly translated into immersive reading artifacts for our teams and our customers. A world where a group of Nigerian teenagers narrates their 4C story in a shared universe of novels that are read by millions.

This isn’t possible just yet. OpenAI’s GPT-3 model has an almost magical capability to generate endless streams of plausible, interesting text, but it is currently limited to no more than 2048 tokens per request (1500 words). As I understand it, the computing resources required for the key “self-attention” step currently scale on a (mostly) quadratic basis, which means that doubling the size of the request equals quadrupling the response time. So–check my work, please, OpenAI!–creating a “long-form” completion the size of an 80,000-word book– 53x larger–would require 53^2 (2809x) more resources. Increasing speed by three orders of magnitude is a big deal, but the history of computing technology suggests this will happen eventually, and probably in a timeframe of a few to several years rather than multiple decades. So an abundance of long-form narrative is coming; the only question is when, who and how. OpenAI has a laudable focus on safety, and managing risk is important, but it’s also time to lift our eyes to the horizon and begin creating wonders.

I do have some ideas about how to move forward. For example (and in no particular order) a few thoughts.

Book proposals are, in essence, two to six page “prompts” with many common structural, functional, and semantic elements (see e.g. Rosenfeld 2021; O’Reilly 2021; Rein 2017). It should be possible with a suitable corporate partner to obtain a collection or collection of book proposals and compare them to a) finished manuscripts b) measures of book quality and commercial success via c) machine learning.


Inversely, Cliff Notes and summaries are like prompts with the quality baked out. We need to learn how to set an adjustable quality floor. I know there has been extensive research on “idea density” and cognition. Idea density in diaries has successfully predicted resistance to Alzheimer’s (Snowdon 1996).

Codex-style books are highly structured encodings of several hundred years of usability and educational experience and knowledge. The Chicago Manual of Style identifies no fewer than 40 “parts of the book” such as acknowledgments, table of contents, and so forth (U. of Chicago 2020) and of course there are myriad variations and special circumstances. My PageKicker software had rules to govern how each part of the book was sourced and formatted. Each chapter requires dozens of substantive decisions. The combinatorial nature of this task seems amenable to reinforcement learning. Agents could explore millions of possible sequences — a sort of super-editing.
The actual process of writing a book is iterative and the incremental outputs required are within the current performance capabilities of GPT-3. Even Stephen King writes only ten pages a day (every day). I envisage a process of nested iteration:

* Author develops book proposal or prospectus together with Muse
* Muse & author together generate various alternative chapter outlines
* Muse generates section by section outlines for each chapter identifying key topics and key points
* Muse generates first draft for each section in page-by-by format, author edits, approves, takes responsibility for each word
* Muse learns from what author does, and recommends potential changes to total structure — “you seem to really like my how-to sections, do you want to add more of them”? “are you sure this is really a book about product management? It seems like you are more interested in user experience testing.”
* Ultimately, reader input is shared with Muse & human author.

I am not wedded to this particular process. Maybe GPT-3 or 4 is already capable of creating coherent long-form generations without user dialogue! It does pretty well sometimes within the 2048-token limit. I would recommend starting with relatively structured and short works like short stories, plays, or screenplays. I am an alumnus of USC’s School of Cinema Production so I might start there.


From what I’ve read about recent research in long-form transformers, people are trying to get around the quadratic self-attention problem by increasing efficiency (Tay 2020); sampling strategies (Xiong 2021; Zaheer 2020; Beltagy 2020); and by domain-specific pretraining vocabularies and layer design as in MedBERT (Rasmy 2020). Maybe the next step towards long-form narrative fiction is creating sampling strategies that leverage the inherent structure of various types of long form documents. For example, government reports usually have Executive Summaries; nonfictions books usually have tables of contents and introductions; modern plays have three acts, classics five, with crises at the end of each act (Egri 1972); the most revealing section of a SEC 10-K filing is usually the “risks” section; and so on. Similarly, it would seem that semantically aware self-attention model for longform fiction should be directed to passages that define a character’s goals and internal conflicts (McKee 1999); an author’s style (Dickens 1859); unique setting and “world-building” (Tolkien 1955); moral insight (Rowling 2007). A more challenging, and vexing, question is whether longform self-attention should be informed by information and values “outside the prompt”, such as an author’s approach to representation, inclusion, and diversity (Twain 1884; Rowling 2020). The development of these technologies will not be without risk.


Given this logic, it would seem that a sensible strategy to make longform tractable in the near term would be to pick an existing model such as GPT-3 and plug in a custom self-attention module tuned for a couple of domains (narrative fiction and nonfiction, perhaps).


This is within reach.


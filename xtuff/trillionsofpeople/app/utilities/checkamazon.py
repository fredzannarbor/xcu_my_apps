   if checkamazon:
        print('checking amazon')

        number_of_titles = cumulative_df['title'].count()

        titlelist = cumulative_df['title'].tolist()
        try:               
            checkresults = check_if_titles_are_in_amazon(titlelist)

            #checkresults['title'] = titlelist
            print('checkresults', checkresults)
        except Exception as e:
            print('Amazon title lookup failed', e)
    else:
        print('not checking amazon for catalog & comparable info')

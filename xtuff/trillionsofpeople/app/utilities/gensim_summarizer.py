# gensim summarizer
import chardet
from gensim.summarization.summarizer import summarize


def gensim_summarizer(text, wordcount):
    summary = summarize(text, word_count=wordcount, split=False)

    return summary


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='Nimble Standard')
    parser.add_argument('--infile', '-i', type=str, default='../data/input.txt', help="input file")
    parser.add_argument('--outfile', '-o', type=str, default='../data/output.txt', help="output file")
    parser.add_argument('--datadir', '-d', type=str, default='../data', help="data directory")
    parser.add_argument('--tmpdir', '-t', type=str, default='/tmp', help="temporary directory")
    parser.add_argument('--logdir', '-l', type=str, default='../logs', help="log directory")
    #parser.add_argument('--logfile', '-f', type=str, default='nimble.log', help="log file")

    parser.add_argument('--wordcount', '-n', type=int, default=800, help="max number of words")


    args = parser.parse_args()

    infile = args.infile
    outfile = args.outfile
    datadir = args.datadir
    tmpdir = args.tmpdir
    logdir = args.logdir
    wordcount = args.wordcount
    #logfile = args.logfile'

    file_encoding = chardet.detect(
        open(infile, 'rb').read())['encoding']

    print(file_encoding)

    # read in the file with encoding = file_encoding
    with open(infile, encoding=file_encoding, errors="ignore") as f:
        text = f.read()
        len(text)


    summary = gensim_summarizer(text, wordcount)
    print(summary)

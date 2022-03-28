from pyspark import SparkContext, SparkConf
import sys
import os
import random as rand


def format_and_filter_doc(document, K=-1):
    product_costumer_set = set()
    for line in document.split('\n'):
        fields = document.split('\n')
        product = fields[1]
        count = fields[3]
        costumer = fields[6]
        country = fields[7]
        if (count > 0 and (country == S or country == "all") and ((product,costumer) not in product_costumer_set[product])):
            product_costumer_set.add((product,costumer))
    if K == -1:
        return [(p, c) for p,c in product_costumer_set]
    else:
        return [(rand.randint(0, K - 1), (p, c)) for p,c in product_costumer_set]

def word_count_per_doc(document, K=-1):
    pairs_dict = {}
    for word in document.split(' '):
        if word not in pairs_dict.keys():
            pairs_dict[word] = 1
        else:
            pairs_dict[word] += 1
    if K == -1:
        return [(key, pairs_dict[key]) for key in pairs_dict.keys()]
    else:
        return [(rand.randint(0, K - 1), (key, pairs_dict[key])) for key in pairs_dict.keys()]


def gather_pairs(pairs):
    pairs_dict = {}
    for p in pairs[1]:
        word, occurrences = p[0], p[1]
        if word not in pairs_dict.keys():
            pairs_dict[word] = occurrences
        else:
            pairs_dict[word] += occurrences
    return [(key, pairs_dict[key]) for key in pairs_dict.keys()]


def gather_pairs_partitions(pairs):
    pairs_dict = {}
    for p in pairs:
        word, occurrences = p[0], p[1]
        if word not in pairs_dict.keys():
            pairs_dict[word] = occurrences
        else:
            pairs_dict[word] += occurrences
    return [(key, pairs_dict[key]) for key in pairs_dict.keys()]


def filter(dataset):
    test = (docs.flatMap(word_count_per_doc))
    return test

def word_count_1(docs):
    word_count = (docs.flatMap(word_count_per_doc)  # <-- MAP PHASE (R1)
                  .reduceByKey(lambda x, y: x + y))  # <-- REDUCE PHASE (R1)
    return word_count


def word_count_2(docs, K):
    word_count = (docs.flatMap(lambda x: word_count_per_doc(x, K))  # <-- MAP PHASE (R1)
                  .groupByKey()  # <-- SHUFFLE+GROUPING
                  .flatMap(gather_pairs)  # <-- REDUCE PHASE (R1)
                  .reduceByKey(lambda x, y: x + y))  # <-- REDUCE PHASE (R2)
    return word_count


def word_count_3(docs, K):
    word_count = (docs.flatMap(word_count_per_doc)  # <-- MAP PHASE (R1)
                  .groupBy(lambda x: (rand.randint(0, K - 1)))  # <-- SHUFFLE+GROUPING
                  .flatMap(gather_pairs)  # <-- REDUCE PHASE (R1)
                  .reduceByKey(lambda x, y: x + y))  # <-- REDUCE PHASE (R2)
    return word_count


def word_count_with_partition(docs):
    word_count = (docs.flatMap(word_count_per_doc)  # <-- MAP PHASE (R1)
                  .mapPartitions(gather_pairs_partitions)  # <-- REDUCE PHASE (R1)
                  .groupByKey()  # <-- SHUFFLE+GROUPING
                  .mapValues(lambda vals: sum(vals)))  # <-- REDUCE PHASE (R2)

    return word_count


def main():
    # CHECKING NUMBER OF CMD LINE PARAMETERS
    assert len(sys.argv) == 5, "Usage: python G042HW1.py <K> <H> <S> <file_name>"

    # SPARK SETUP
    conf = SparkConf().setAppName('WordCountExample').setMaster("local[*]")
    sc = SparkContext(conf=conf)

    # INPUT READING

    # 1. Read number of partitions
    K = sys.argv[1]
    assert K.isdigit(), "K must be an integer"
    K = int(K)

    # 2. Read H
    H = sys.argv[2]
    assert H.isdigit(), "H must be an integer"
    H = int(H)

    # 3. Read S
    S = sys.argv[3]

    # 4. Read input file and subdivide it into K random partitions
    data_path = sys.argv[4]
    assert os.path.isfile(data_path), "File or folder not found"

    dataset = sc.textFile(data_path, minPartitions=K).cache()
    dataset.repartition(numPartitions=K)

    # SETTING GLOBAL VARIABLES
    numdocs = dataset.count();
    print("Number of documents = ", numdocs)

    print("Number of distinct words in the documents using reduceByKey =", filter(dataset[0],S,K).groupByKey().mapValues(lambda x: (x,1)))

'''
    # STANDARD WORD COUNT with reduceByKey
    print("Number of distinct words in the documents using reduceByKey =", word_count_1(docs).count())

    # IMPROVED WORD COUNT with groupByKey
    print("Number of distinct words in the documents using groupByKey =", word_count_2(docs, K).count())

    # IMPROVED WORD COUNT with groupBy
    print("Number of distinct words in the documents using groupBy =", word_count_3(docs, K).count())

    # WORD COUNT with mapPartitions
    wordcount = word_count_with_partition(docs)
    numwords = wordcount.count()
    print("Number of distinct words in the documents using mapPartitions =", numwords)

    # COMPUTE AVERAGE WORD LENGTH
    average_word_len = wordcount.keys().map(lambda x: len(x)).reduce(lambda x, y: x + y)
    print("Average word length = ", average_word_len / numwords)
'''

if __name__ == "__main__":
    main()

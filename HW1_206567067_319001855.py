from collections import defaultdict
import os

class InvertedIndex:
    
    def __init__(self, collection_path):
        """
        Initialize the inverted index from the AP collection.

        During index construction, specifically, for building the posting lists you should use successive integers as
        document internal identifiers (IDs) for optimizing query processing, as taught in class, but you still need to
        be able to get the original document ID when required.

        :param collection_path: path to the AP collection
        """
        self.documents = {}
        self.posting_list = defaultdict(list)
        
        Texts = self.parse_text(collection_path)
        i=0
        for text in Texts:
            for document in self.TrecTextIterator(text):
                contents, internal_id = self.extract_text_and_id(document)
                internal_id = internal_id.strip()
                self.documents[i] = {"contents": contents, "internal_id": internal_id}
                self.update_posting_list(contents, i)
                i+=1
        self.sort_posting_list()

    def top_bottom_n_terms(self, n=10,top=True):
        term_frequencies = {term: len(doc_ids) for term, doc_ids in list(self.posting_list.items())}
        sorted_terms = sorted(term_frequencies.items(), key=lambda term_and_doc_freq: (term_and_doc_freq[1],term_and_doc_freq[0]), reverse=top)[:n] # reverse determines order, so get top or not
        return sorted_terms


    def update_posting_list(self, document, doc_id):
        terms = document.split() 
        for term in terms:
            if term:
                self.posting_list[term].append(doc_id)

    def sort_posting_list(self):
        for term in self.posting_list:
            self.posting_list[term] = sorted(list(set(self.posting_list[term])), key=lambda x: (x, self.documents[x]), reverse=False)

    def extract_text_and_id(self, doc):
        text = []
        doc = ' '.join(doc.split('\n')) #remove newlines
        internal_id, contents = doc.split('</DOCNO>')
        contents = contents.replace('<DOC>', '').replace('</DOC>', '').replace('<TEXT>', '').replace('</TEXT>', '')
        return contents, internal_id

    def get_posting_list(self, term):
        """
        Return the posting list for the given term from the index.
        If the term is not in the index, return an empty list.
        :param term: a word
        :return: list of document ids in which the term appears
        """
        return self.posting_list.get(term, [])

    class TrecTextIterator:
        def __init__(self, trectext):
            self.trectext = trectext
            self.doc_start = '<DOCNO>'
            self.doc_blocks = trectext.split(self.doc_start)[1:]
            self.current_doc = None
            
        def __iter__(self):
            return self

        def __next__(self):
            if len(self.doc_blocks)>0:
                self.current_doc =  self.doc_blocks[0]
                self.doc_blocks = self.doc_blocks[1:]
                return self.current_doc
            else:
                raise StopIteration

    def parse_text(self, collection_path):
        texts = []
        for filename in os.listdir(collection_path):
            with open(os.path.join(collection_path, filename), 'r') as file:
                texts.append(file.read())
        return texts



# Part 2: Boolean Retrieval Model
class BooleanRetrieval:
    def __init__(self, inverted_index):
        """
        Initialize the boolean retrieval model.
        """
        self.inverted_index = inverted_index
        self.all_docs = [i for i in range(len(inverted_index.documents))]
        
    def eval_boolean_query(self, query):
        stack = []
        operators = {'AND', 'OR', 'NOT'}
        query = query.replace('\n', '').split(' ')
        for word in query:
            if word not in operators:
                stack.append(self.inverted_index.posting_list[word.lower()])
            else:
                if word == 'AND':
                    list2 = stack.pop()
                    list1 = stack.pop()
                    stack.append(BooleanRetrieval.and_query(list1, list2))
                elif word == 'OR':
                    list2 = stack.pop()
                    list1 = stack.pop()
                    stack.append(BooleanRetrieval.or_query(list1, list2))
                elif word == 'NOT':
                    list1 = stack.pop()
                    stack.append(BooleanRetrieval.not_query(self.all_docs, list1))
        if len(stack) ==2:
            list2 = stack.pop()
            list1 = stack.pop()
            stack.append(BooleanRetrieval.and_query(list1, list2))
        return stack.pop()

    def run_query(self, query):
        """
        Run the given query on the index.
        :param query: a boolean query
        :return: list of document ids
        """
        return [self.inverted_index.documents[_id]["internal_id"] for _id in self.eval_boolean_query(query)]
    
    @staticmethod
    def and_query(ordered_list1, ordered_list2):
            res = []
            l1, l2 = 0, 0
            while l1 < len(ordered_list1) and l2 < len(ordered_list2):
                if ordered_list1[l1] == ordered_list2[l2]:
                    res.append(ordered_list1[l1])
                    l1 += 1
                    l2 += 1
                elif ordered_list1[l1] < ordered_list2[l2]:
                    l1 += 1
                else:
                    l2 += 1
            return res
    @staticmethod    
    def or_query(ordered_list1, ordered_list2):
        res = []
        l1, l2 = 0, 0
        while l1 < len(ordered_list1) and l2 < len(ordered_list2):
            if ordered_list1[l1] == ordered_list2[l2]:
                res.append(ordered_list1[l1])
                l1 += 1
                l2 += 1
            elif ordered_list1[l1] < ordered_list2[l2]:
                res.append(ordered_list1[l1])
                l1 += 1
            else:
                res.append(ordered_list2[l2])
                l2 += 1
        return res + ordered_list1[l1:] + ordered_list2[l2:]
    @staticmethod
    def not_query(all_docs, ordered_list2):
        res = []
        l1, l2 = 0, 0
        while l1 < len(all_docs) and l2 < len(ordered_list2):
            if all_docs[l1] == ordered_list2[l2]:
                l1 += 1
                l2 += 1
            elif all_docs[l1] < ordered_list2[l2]:
                res.append(all_docs[l1])
                l1 += 1
            else:
                l2 += 1
        return res + all_docs[l1:]
            

    
    
    
if __name__ == "__main__":

    # TODO: replace with the path to the AP collection and queries file on your machine
    path_to_AP_collection = '/data/HW1/AP_Coll_Parsed'
    path_to_boolean_queries = '/data/HW1/BooleanQueries.txt'
    # Part 1
    inverted_index = InvertedIndex(path_to_AP_collection) # TODO: uncomment!!!
    
    # # Load the object from a file
    # with open('inverted_index.pkl', 'rb') as file:
    #     inverted_index = pickle.load(file)
    # Part 2
    boolean_retrieval = BooleanRetrieval(inverted_index=inverted_index)

    # Read queries from file
    with open(path_to_boolean_queries, 'r') as f:
        queries = f.readlines()

    # Run queries and write results to file
    with open("Part_2.txt", 'w') as f:
        for query in queries:
            result = boolean_retrieval.run_query(query)
            f.write(' '.join(result) + '\n')

    # Part 3
    ## part 1
    top_ten_terms = inverted_index.top_bottom_n_terms(n=10,top=True)
    with open("Part_3a.txt", 'w') as f:
        for term, freq in top_ten_terms:
            f.write(f"{term}: {freq}\n")
    ## part 2 
    bottom_ten_terms = inverted_index.top_bottom_n_terms(n=10,top=False)
    with open("Part_3b.txt", 'w') as f:
        for term, freq in bottom_ten_terms:
            f.write(f"{term}: {freq}\n")
import json
import random


class Generator():
    '''
    Text generator using markov chains from the work of Omer Nevo accessible here (https://www.youtube.com/watch?v=-51qWZdA8zM)
    '''

    def __init__(self, order, filename, length):
        self.order = order
        self.filename = filename
        self.length = length
        self.group_size = self.order + 1
        self.text = None
        self.graph = {}
        return


    def train(self, filename):
        self.text = open(f'bio_files/{filename}_Biographies.txt', encoding='utf8').read().split()
        self.text = self.text + self.text[:self.order]

        for i in range(0, len(self.text) - self.group_size):
            key = tuple(self.text[i:i + self.order])
            value = self.text[i + self.order]
            if key in self.graph:
                self.graph[key].append(value)
            else:
                self.graph[key] = [value]
        return


    def generate(self, length):
        index = random.randint(0, len(self.text) - self.order)
        result = self.text[index:index + self.order]
        
        for i in range(length - 1):
            state = tuple(result[len(result) - self.order:])
            next_word = random.choice(self.graph[state])
            result.append(next_word)
        return " ".join(result[self.order:])


    def evaluate_order(self):
        '''
        Method that allows me to evaluate the range of order to use.
        '''

        nb_states = len(self.graph.keys())
        total_options = 0

        for key in self.graph.keys():
            total_options += len(self.graph[key])

        avg = total_options / nb_states
        if avg > 2:
            result = f"Bon"
            # result = f"Nombre moyen d'options par state : {avg} - Bon"
        elif avg > 1.5:
            result = f"Correct"
            # result = f"Nombre moyen d'options par state : {avg} - Correct"
        elif avg > 1.1:
            result = f"Très limite"
            # result = f"Nombre moyen d'options par state : {avg} - Très limite"
        else:
            result = f"Order trop élevé !"
            # result = f"Nombre moyen d'options par state : {avg} - Order trop élevé !"
        return result



    def proceed(self):
        '''
        "Master function" that calls the rest of the class.
        '''
        self.train(filename=self.filename)
        order_eval = self.evaluate_order()
        
        while order_eval not in ["Bon", "Correct"]:
            self.order -= 1
            self.group_size = self.order + 1
            self.graph = {}
            self.train(filename=self.filename)
            order_eval = self.evaluate_order()

        print(self.generate(length=self.length))
        print('choosen order : ', self.order) # need to delete

if __name__ == '__main__':
    gen = Generator(order=4, filename='Simon', length=100)
    gen.proceed()
    keys = [str(key) for key in gen.graph.keys()]
    values = [value for value in gen.graph.values()]
    print(keys[0], values[0])
    dico = {}
    for i in range(len(keys)):
        dico[keys[i]] = values[i]
    with open('devTests/graph.json', 'w') as f:
        json.dump(dico, f, indent=4)


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

        for key in gen.graph.keys():
            total_options += len(gen.graph[key])

        avg = total_options / nb_states
        if avg > 2:
            result = f"Nombre moyen d'options par state : {avg} - Bon"
        elif avg > 1.5:
            result = f"Nombre moyen d'options par state : {avg} - Correct"
        elif avg > 1.1:
            result = f"Nombre moyen d'options par state : {avg} - Très limite"
        else:
            result = f"Nombre moyen d'options par state : {avg} - Order trop élevé !"
        return result


    def proceed(self):
        '''
        "Master function" that calls the rest of the class.
        '''

        self.train(filename=self.filename)
        print(f'Order : {self.order}\nFilename : {self.filename}\nLength : {self.length}')
        print(self.evaluate_order())
        print('\n')
        print(self.generate(length=self.length))

if __name__ == '__main__':
    gen = Generator(order=2, filename='Simon', length=100)
    gen.proceed()
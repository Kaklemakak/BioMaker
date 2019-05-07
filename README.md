# Biography Generator
[WIP]
The goal of this project is to generate biographies based on biographies of real person with same first name.

---

The **client.py** file purpose is to collect biographies on wikipedia.  
The **markov.py** file generate a text based on the gathered biographies.

---
- The **client.py** works only for french wikipedia for now.  
I plan to make it works for english and eventually other languages.

- The generated text are primitive and senseless for now since i need to add more complexity to the generator.  
I plan to use Ontology with Spacy to achieve this.

---
To make this works you'll need the wikipedia library by Jonathan Goldsmith available here : [https://pypi.org/project/wikipedia/](https://pypi.org/project/wikipedia/)

The Markov part comes from the work of Omer Nevo available here : [Poetry in Python: Using Markov Chains to Generate Texts by Omer Nevo](https://www.youtube.com/watch?v=-51qWZdA8zM)

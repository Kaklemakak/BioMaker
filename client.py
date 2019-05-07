import json
import re
import requests
import time
import wikipedia


wikipedia.set_lang('fr')

class Wikiclient(object):
    '''
    This client is responsible for browsing all the wikipedia pages concerning the given first_name in order to retrieve all the biographies. 
    All methods containing a 'debug' attribute will be modified for 'production' version:
    each parts following an 'if debug:' are only present for development purposes and will be removed from the 'production' version.
    '''

    def __init__(self, first_name):
        self.first_name = first_name
        self.pages_list = [first_name]
        self.homonyms_pages_list = []
        self.biography = ''


    def api_parse(self, page=''):
        '''
        Call to the Wikimedia API.
        Parse the categories and sections of a wikipedia page.
        '''

        session = requests.Session()
        URL = "https://fr.wikipedia.org/w/api.php"

        PARAMS = {
            'action': "parse",
            'page': page,
            'prop': {
                'categories|sections'
            },
            'format': "json"
        }

        response = session.get(url=URL, params=PARAMS)
        DATA = response.json()

        return DATA


    def get_pages(self, name='', apfrom='', debug=False):
        ''' 
        API call to get the list of wikipedia pages which names start with the given first_name. 
        The returned list contain a maximum of 500 names, if the total list is longer, a 'continue' name is also returned.
        If a 'continue' name is returned, the method will call herself with the 'continue' name as her 'apfrom' attribute to catch the following 500 names.
        Currently the gathered pages_list contains all groups of names in reversed order, which doesn't impact the following.
        '''

        if debug:
            start_time = time.time()
            print('>>> Function get_pages <<<')
        session = requests.Session()
        URL = "https://fr.wikipedia.org/w/api.php"

        PARAMS = {
            'action': "query",
            'list': 'allpages',
            'apprefix': name,
            'aplimit': 500,
            'format': "json"
        }

        if apfrom:
            PARAMS['apfrom'] = apfrom

        response = session.get(url=URL, params=PARAMS)
        DATA = response.json()
        
        if 'continue' in DATA:
            if debug:
                print('Continue from :', DATA['continue']['apcontinue'])
                self.get_pages(name=name, apfrom=DATA['continue']['apcontinue'], debug=True)
            else:
                self.get_pages(name=name, apfrom=DATA['continue']['apcontinue'])
        for page in DATA['query']['allpages']:
            self.pages_list.append(page['title'])

        if debug:
            print("--- Temps d'execution pour get_pages() : %s secondes ---" % (time.time() - start_time))
        return self.pages_list


    def gather_biographies(self, debug=False):
        '''
        Gather all biographies for names in pages_list and save them in a file. 

        Call api_parse for each name in pages_list and check if the page concern a person.
        If so, also checks if the page contains a 'Biographie' section.
        Than gather Biographie from section and subsections in exists or directly from page content.
        '''

        if debug:
            start_time = time.time()
            print('>>> Function gather_biographies <<<')
        for name in self.pages_list:
            if debug:
                print('Checking page', name)
            page = self.api_parse(name)
            if 'error' not in page:
                if self.is_a_person(page=page):
                    section_number = self.has_biography_section(page=page)
                    if section_number:
                        if debug:
                            self.get_biography_section_and_sub_sections(page=page, section_number=section_number, debug=True)
                        else:
                            self.get_biography_section_and_sub_sections(page=page, section_number=section_number)
                    else:
                        if debug:
                            self.get_biography_from_content(page=page, debug=True)
                        else:
                            self.get_biography_from_content(page=page)
                elif debug:
                    print("/!\ The page", name, "doesn't concern a person.")
            elif debug:
                print("/!\ The page", name, "returns an error :", page['error'])
        if debug:
            print("--- Temps d'execution pour gather_biographies() : %s secondes ---" % (time.time() - start_time))


    def is_a_person(self, page='', debug=False):
        ''' 
        Check if the page concern a person or else. 
        For now, the only way i found to do so is to check for 'Birth' or 'Death' in categories.
        '''

        if debug:
            start_time = time.time()
            print('>>> Function is_a_person <<<')
        categories = page['parse']['categories']
        categories_to_check = len(categories)

        for category in categories:
            categories_to_check -= 1
            if "Naissance" in category['*'] or "Décès" in category['*']:
                if debug:
                    print("--- Temps d'execution pour is_a_person() : %s secondes ---" % (time.time() - start_time))
                return True
            elif categories_to_check == 0:
                if debug:
                    print("--- Temps d'execution pour is_a_person() : %s secondes ---" % (time.time() - start_time))
                return False
    
    
    def has_biography_section(self, page='', debug=False):
        ''' Check if the page contains a 'Biographie' section. '''

        if debug:
            start_time = time.time()
            print('>>> Function has_biography_section <<<')
        sections = page['parse']['sections']
        sections_to_check = len(sections)

        for section in sections:
            sections_to_check -= 1
            if "Biographie" in section['line']:
                if debug:
                    print("--- Temps d'execution pour has_biography_section() : %s secondes ---" % (time.time() - start_time))
                return section['number']
            elif sections_to_check == 0:
                if debug:
                    print("--- Temps d'execution pour has_biography_section() : %s secondes ---" % (time.time() - start_time))
                return False


    def get_biography_section_and_sub_sections(self, page='', section_number='', debug=False):
        '''
        Gather 'Biographie' section and sub-sections contents.

        We start by generating a regex to catch not only the 'Biographie' section but also the sub-sections.
        We also need to clean sections names to avoid problem with 'irregular' or 'buggy' wikipedia pages.

        Once we get all the biographie related sections number we fetch their content with the help of the wikipedia library (https://pypi.org/project/wikipedia/)
        We need to do it in a particular way to avoid problems with some pages (see commented code l.202)
        Than we check for empty sections or sub-sections (some wikipedia pages contains sections that are created only to design a title).
        Finally the gathered biographie is added to a file named '{first_name}_Biographies.txt' in the 'bio_files' folder.
        '''

        if debug:
            start_time = time.time()
            print('>>> Function get_biography_section_and_sub_sections <<<')
        biography_sections = []
        sub_sections_regex = r'^([' + re.escape(str(section_number)) + r']){1}([.]{1}[\d]*)*$'
        for section in page['parse']['sections']:
            if re.match(sub_sections_regex, section['number']):
                section_name = re.sub(r'<.*?>', '', section['line'])                # small clean of sections names (delete html)
                section_name = re.sub(r'(&nbsp;)', ' ', section_name)               # small clean of sections names (delete '&nbsp;')
                biography_sections.append(section_name)

        title = page['parse']['title']
        if debug:
            print('get bio for :', title)
        pattern = "<WikipediaPage '" + title + "'>"
        wpage = wikipedia.page(title)
        if str(wpage) == pattern:
            # The previous lines (196-201) are here to avoid problems with some pages leading to a Disambiguation error 
            # ex: 'Antoine-Charles de Saint-Simon' leads to page 'Saint-Simon', the real page is 'Antoine-Charles (Saint-Simon)'
            # The Disambiguation error raise has also been deactivated in wikipedia.py line 393
            for section in biography_sections:                                      
                if wpage.section(section) is not None and len(wpage.section(section)) > 0: # To avoid empty section and sub-sections (in case of sub-sub-sections...)
                    self.biography += wpage.section(section)
        elif debug:
            print('/!\ Not the exact page name.')

        with open(f'bio_files/{self.first_name}_Biographies.txt', 'a', encoding='utf-8') as f:
            if self.biography:
                f.write(self.biography)
                f.write('\n\n')
                self.biography = ''
        if debug:
            print("--- Temps d'execution pour get_biography_section_and_sub_sections() : %s secondes ---" % (time.time() - start_time))


    def get_biography_from_content(self, page='', debug=False):
        '''
        Method used to gather biographies from pages which doesn't contain a 'Biographie' section.

        We need to gather the summary and the content minus specials sections we want to avoid.
        As in get_biography_section_and_sub_sections we fetch the content with the wikipedia library (https://pypi.org/project/wikipedia/),
        and still need our little workaround to avoid some errors.
        We fetch the sections list, seek for all the unwanted sections and delete them from the list.
        The summary of the page and the content of all the sections in the list (empty sections are also avoided),
        are than added to a file named '{first_name}_Biographies.txt' in the 'bio_files' folder.
        '''

        if debug:
            start_time = time.time()
            print('>>> Function get_biography_from_content <<<')
        unwanted_sections = ['Filmographie',
                            'Bibliographie',
                            'Œuvres',
                            'Distinctions',
                            'Nominations',
                            'Voir aussi',
                            'Articles connexes',
                            'Notes et références',
                            'Liens externes']


        title = page['parse']['title']
        if debug:
            print('get content for :', title)
        pattern = "<WikipediaPage '" + title + "'>"
        wpage = wikipedia.page(title)
        if str(wpage) == pattern:
            # To avoid problems with some pages leading to a DisambiguationError or to a PageError
            # DisambiguationError ex: 'Antoine-Charles de Saint-Simon' leads to page 'Saint-Simon', the real page is 'Antoine-Charles (Saint-Simon)'
            # PageError ex: 'Simon-Auguste de Lippe' is not found and leads to a page error...
            # The DisambiguationError and PageError raise have also been deactivated in wikipedia.py line 275, 346, 349 and 393
            regex_list = []
            sections_list = [section for section in page['parse']['sections']]

            # look for undesired sections
            for section in sections_list:
                if section['line'] in unwanted_sections:
                    regex = r'^((' + re.escape(str(section['number'])) + r')){1}([.]{1}[\d]*)*$'
                    regex_list.append(regex)

            # delete unwanted sections from list
            for regex in regex_list:
                for section in reversed(sections_list):
                    if re.match(regex, section['number']) or wpage.section(section['line']) is None:
                        sections_list.pop(sections_list.index(section))

            with open(f'bio_files/{self.first_name}_Biographies.txt', 'a', encoding='utf-8') as f:
                f.write(wpage.summary)
                for section in sections_list:
                    section_content = wpage.section(section['line'])
                    if section_content is not None:
                        f.write(section_content)
                f.write('\n\n')

        elif debug:
            print('/!\ La page ne porte pas exactement ce nom')
        if debug:
            print("--- Temps d'execution pour get_biography_from_content() : %s secondes ---" % (time.time() - start_time))


    def get_all_biographies(self, debug=False):
        '''
        "Master function" that calls the rest of the client.

        Find all wikipedia pages which name start with the first name.
        Gather biography for each page and save in a file.

        Really verbose for now has i test it only in terminal, when i'll give it an UI it will be shorter and cleaner.
        '''

        if debug:
            start_time = time.time()
            print('>>> Function get_all_biographies <<<')
            self.get_pages(name=self.first_name, debug=True) # disable for rapidity tests
            print('number of pages :', len(self.pages_list))
            go_on = input('Doit-on récupérer tout ça ? (oui/non) --- ').lower()
            accept = ['oui', 'o', 'ok']
            if go_on in accept:
                self.gather_biographies(debug=True)
            else:
                save_list = input('Sauvegarder la liste de pages dans un fichier ? (oui/non) --- ').lower()
                if save_list in accept:
                    with open(f'pages_lists/{self.first_name}s_list.txt', 'w', encoding='utf-8') as f:
                        for page in self.pages_list:
                            f.write(page)
                            f.write('\n')
            print("--- Temps d'execution total : %s secondes ---" % (time.time() - start_time))
        else:
            start_time = time.time()
            self.get_pages(name=self.first_name) # disable for rapidity tests
            print('number of pages :', len(self.pages_list))
            go_on = input('Doit-on récupérer tout ça ? (oui/non) --- ').lower()
            accept = ['oui', 'o', 'ok']
            if go_on in accept:
                self.gather_biographies()
            print("--- Temps d'execution total : %s secondes ---" % (time.time() - start_time))


if __name__ == '__main__':
    first_name = input('Quel Prénom souhaiter vous rechercher ?\n').capitalize()
    Wikiclient(first_name).get_all_biographies(debug=False)
    

    # # Rapidity Tests
    # client = Wikiclient('Fernand Augereau')
    # client.pages_list = ['Fernand Augereau', 'Fernand Melgar', 'Fernandos', 'Hôpital Fernand-Widal']
    # client.get_all_biographies(debug=True)
    
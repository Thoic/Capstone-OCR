def assemble_words(paragraph):
    assembled_words=''
    for word in paragraph.words:
        assembled_word=''
        for symbol in word.symbols:
            assembled_word += symbol.text
        assembled_words += assembled_word + ' '
    return assembled_words.strip()

def find_words_location(document, words_to_find):
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                assembled_words = assemble_words(paragraph)
                if words_to_find in assembled_words:
                    return paragraph.bounding_box

def assemble_word(word):
    assembled_word=""
    for symbol in word.symbols:
        assembled_word += symbol.text
    return assembled_word

def find_word_location(document, word_to_find):
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    assembled_word = assemble_word(word)
                    if(assembled_word == word_to_find):
                        return word.bounding_box
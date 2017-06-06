from sentenceEmbedding import get_sentence_vector
from scipy import spatial
import re
import functools
import random
import pandas as pd
from data_preprocess.get_cms_news import clearify


def cosine_distance(v1, v2):
    try:
        distance = spatial.distance.cosine(v1, v2)
    except ValueError:
        distance = float('inf')

    return distance


def sentence_is_same(string1, string2):
    v1 = get_sentence_vector(string1)
    v2 = get_sentence_vector(string2)
    return cosine_distance(v1, v2) < 1e-1


def line_to_sentences(line):
    white_space_regex = re.compile(r'[\n\r\t\xa0@]')
    splited_mark = re.compile(r"""[,，。；、？！?？|;!！<> · () （）]""")
    content = white_space_regex.sub(" ", line)
    content = splited_mark.sub(" ", content)
    content = re.sub("\s+", ' ', content).strip()
    return content.split()


def get_text_sentence(text_file_name):
    lines = [line for line in open(text_file_name).readlines()]
    add = lambda a, b: a + b
    text_sentences = functools.reduce(add, map(line_to_sentences, lines), [])
    return text_sentences


def get_text_vector(text):
    return get_sentence_vector(text)


def get_text_sentences_distances(text, sentences):
    text_vector = get_text_vector(text)
    sentences_vectors = [get_sentence_vector(string) for string in sentences]
    text_sentences_distances = [cosine_distance(vec, text_vector) for vec in sentences_vectors]
    return list(zip(sentences, text_sentences_distances))


def get_all_sentences_distance(text_sentences):
    sentence_distances = get_text_sentences_distances(" ".join(text_sentences), text_sentences)
    sentence_distance_dic = {sentence: distance for sentence, distance in sentence_distances}
    return sentence_distance_dic


def clarify_duplicate_sentences(sentences_sorted_by_importance):
    deleted_index = []
    for index in range(len(sentences_sorted_by_importance) - 1):
        current_string = sentences_sorted_by_importance[index][0]
        next_string = sentences_sorted_by_importance[index + 1][0]
        if sentence_is_same(current_string, next_string):
            deleted_index.append(index + 1)

    for need_del in deleted_index:
        sentences_sorted_by_importance[need_del] = None

    return [s for s in sentences_sorted_by_importance if s is not None]


def get_important_sentences(sentences_distances: dict, keep_ratio=0.9):
    sorted_by_importance = sorted(sentences_distances.items(), key=lambda x: x[1])
    sorted_by_importance = clarify_duplicate_sentences(sorted_by_importance)
    important_sentences = [s for s, d in sorted_by_importance]
    return important_sentences[:int(len(sorted_by_importance)*keep_ratio)]


def get_summary(text_sentences,  summary_length, keep_ratio=0.9):
    sentences_importance = get_all_sentences_distance(text_sentences)
    keep_sentences = get_important_sentences(sentences_importance, keep_ratio=keep_ratio)
    total_sentence_number = 5
    if len(keep_sentences) < total_sentence_number: return keep_sentences
    return get_summary(keep_sentences, summary_length)


def forward_alpha(text : str, index, direction='right'):
    if direction == 'right': index += 1
    else: index -= 1

    if 0 <= index < len(text):
        return text[index].isalpha()

    return False


def get_sentence_begin_index(sub_str: str, text: str, end_marks: list):
    begin_index = text.index(sub_str)
    while begin_index >= 0:
        if text[begin_index] in end_marks: break
        elif text[begin_index] == ' ' and not forward_alpha(text, begin_index, 'left'): break
        begin_index -= 1

    return begin_index


def get_sentence_end_index(sub_str: str, text: str, end_marks: list):
    end_index = text.index(sub_str) + len(sub_str)
    while end_index < len(text):
        if text[end_index] in end_marks: break
        elif text[end_index] == ' ' and not forward_alpha(text, end_index, 'right'): break
        end_index += 1

    return end_index


def find_complete_sentence(sub_sentence: str, text: str) -> str:
    """
    find the complete sentence in the text. 
    What's the complete sentene? sentene between two "end mark", 
        such as .  。 ！ ! ？ ? \space  \n.
        :type sub_sentence: object
    """
    end_marks = ['。', '？', '！', '!', '?', '\n', '\xa0', '\r', '\t']
    begin = get_sentence_begin_index(sub_sentence, text, end_marks) + 1
    end = get_sentence_end_index(sub_sentence, text, end_marks) + 1
    return text[begin: end]


def get_complete_summary(file=None, type="file"):
    if type == 'file':
        text_sentences = get_text_sentence(file)
        text = "".join([line for line in open(file)])
    elif type == 'text':
        text_sentences = clearify(file).split()
        text = file

    summary_length = 60
    summary = get_summary(text_sentences, summary_length=summary_length)
    completed_summary = {}
    for index, sentence in enumerate(text_sentences):
        if sentence in summary:
            complete_sentence = find_complete_sentence(sentence, text)
            completed_summary[complete_sentence] = index

    completed_summary = sorted(completed_summary.items(), key=lambda x: x[1])
    completed_summary = "".join([s for s, _ in completed_summary])

    return completed_summary


def show_summary_in_text(text_sentences, summary):
    for line in text_sentences:
        if len(line) < 1: continue
        if line in summary:
            print(line)
        else:
            print('--{}--'.format(line))


def write_fm_news(f, contents, test_number):
    number = 0
    for row in contents:
        if random.random() < 0.7: continue
        if number > test_number: break

        content = row[1][4]
        if len(content) < 300: continue

        summary = get_complete_summary(content, type='text')
        f.write('--------------------------------------\n')
        f.write("{}\n Content: \n {}\n Description: {}\n".format(number, content, summary))
        print(number)
        number += 1


def get_test_result(content_csv):
    test_file_name = 'summary_test_result_0605.txt'
    contents = pd.read_csv(content_csv)
    contents =  contents.iterrows()
    total_test_length = 25
    with open(test_file_name, 'w') as f:
        write_fm_news(f, contents, total_test_length)


if __name__ == '__main__':
    # summary = get_complete_summary('performace_test/test_summary.txt')
    # print(summary)
    # print('length: {}'.format(len(summary)))
    get_test_result('data_preprocess/updated_news/sqlResult_1262716_0524.csv')
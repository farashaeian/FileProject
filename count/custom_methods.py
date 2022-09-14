from .models import File, Category, Dict
from zipfile import ZipFile
import os
from nltk.tokenize import word_tokenize
from spellchecker import SpellChecker


""" methods were used in uploading zipfile: """

def extract_zip_file(zip_file_obj, user):
    with ZipFile(zip_file_obj.file, mode='r', allowZip64=True) as extracted_file:
        current_user_id = user.id
        extract_path = 'Documents/uploaded_files/user_{0}/'.format(current_user_id)
        extracted_file.extractall(path=extract_path)
    extracted_file.close()


def find_folders(root_folder_path):
    folder_list = []
    for root, dirs, files in os.walk(root_folder_path):
        for d in dirs:
            folder_list.append(os.path.join(root, d))
    return folder_list


def find_files(root_folder_path):
    file_list = []
    for root, dirs, files in os.walk(root_folder_path):
        for f in files:
            file_list.append(os.path.join(root, f))
    return file_list


def text_file_tokenize(file_path):
    opened_file = open(file_path, 'r')
    text = opened_file.read()
    opened_file.close()
    file_text = word_tokenize(text)
    return file_text


def analyze_text_file(file_path, user):
    file_text = text_file_tokenize(file_path)
    analyze = {'new': 0, "duplicate": 0, "typo": 0}
    for word in file_text:
        is_typo = SpellChecker().unknown([word])
        try:
            word_in_Dict = Dict.objects.get(word=word, user=user)
        except Dict.DoesNotExist:
            word_in_Dict = None
        if is_typo:
            # increase typo number in the file
            analyze['typo'] += 1
        elif word_in_Dict:
            # increase word number in the user dictionary
            new_word_number = word_in_Dict.number + 1
            word_in_Dict.number = new_word_number
            word_in_Dict.save()
            # increase word duplication in the file
            analyze['duplicate'] += 1
        else:
            # add new word to the user Dictionary
            new_word = Dict(
                word=word,
                number=1,
                user=user
            )
            new_word.save()
            # increase new word number in the file
            analyze['new'] += 1
    return analyze


def save_folders(folder_list, user):
    for f in folder_list:
        last_slash_index = f.rindex('/')
        folder_father_path = f[:last_slash_index]
        folder_father_obj = Category.objects.get(path=folder_father_path)
        folder_name = f[(last_slash_index + 1):]
        folder_obj = Category(
            path=f,
            display_name=folder_name,
            user=user,
            father=folder_father_obj
        )
        folder_obj.save()


def save_files(file_list, user):
    for f in file_list:
        last_slash_index = f.rindex('/')
        file_category_path = f[:last_slash_index]
        file_category = Category.objects.get(path=file_category_path)
        file_name = f[(last_slash_index + 1):]
        analyze = analyze_text_file(f, user)
        file_obj = File(
            path=f,
            display_name=file_name,
            user=user,
            category=file_category,
            new=analyze['new'],
            duplicate=analyze['duplicate'],
            typo=analyze['typo']
        )
        file_obj.save()

""" methods were used in show folder view: """
""" self is deleted from """

def calculate_folder_info(sent_path):
    # content_list = os.listdir(requested_obj.path)
    # text_file_list = [f for f in content_list if f.endswith(".txt")]

    file_list = []
    for root, dirs, files in os.walk(sent_path):
        for f in files:
            file_list.append(os.path.join(root, f))

    analyze = {
        "display_name": "", "father": 0, 'new': 0, 'duplicate': 0, 'typo': 0
    }
    for f in file_list:
        file_obj = File.objects.get(path=f)
        analyze['new'] = analyze['new'] + file_obj.new
        analyze['duplicate'] = analyze['duplicate'] + file_obj.duplicate
        analyze['typo'] = analyze['typo'] + file_obj.typo
    root_obj = Category.objects.get(path=sent_path)
    analyze['display_name'] = root_obj.display_name
    if root_obj.father:
        analyze['father'] = root_obj.father.id
    else:
        analyze['father'] = ""

    return analyze


def custom_response(obj):
    response_list = []
    pre_content_list = os.listdir(obj.path)
    content_list = []
    # pre_content_list contains first level obj content's "names".
    for x in pre_content_list:
        if x.endswith('.txt'):
            content_list.append(File.objects.get(display_name=x, category=obj))
        else:
            content_list.append(Category.objects.get(display_name=x, father=obj))
    # content_list contains first level content's "objects".
    for y in content_list:
        if y.display_name.endswith('.txt'):
            analyze = {
                "display_name": y.display_name,
                "category": y.category.id,
                "new": y.new,
                "duplicate": y.duplicate,
                "typo": y.typo
            }
            response_list.append(analyze)
        else:
            response_list.append(calculate_folder_info(y.path))  # self. is deleted from beginning of the function
            answer = custom_response(y)  # self. is deleted from beginning of the function
            if answer == []:
                pass
            else:
                response_list.append(answer)
    return response_list

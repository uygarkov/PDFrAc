import os, requests, json, PyPDF2, time, warnings, re, random, string
from habanero import Crossref
from shutil import move


# Randomize file names because it may contain forbidden characters like ?,!,:
def surprise_me(pdf_dir):
    # iterate over all files in directory
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            # generate a random string of length 8 to use as the new filename
            random_string = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
            # rename the file with the random string
            os.rename(os.path.join(pdf_dir, filename), os.path.join(pdf_dir, random_string + '.pdf'))


# Function to get the DOI number of an article using its title
def get_doi(title):
    cr = Crossref()
    res = cr.works(query=title, limit=1)
    try:
        doi = res['message']['items'][0]['DOI']
    except:
        return None
    return doi


# Moves files according to its type
def move_files(directory, filepath, name, option):
    if option == 'duplicate':
        dir_path = directory + r'\duplicates'
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        new_path = dir_path + r'\{}'.format(name)
        if os.path.exists(new_path):
            try:
                os.remove(filepath)
                warnings.warn("multiple duplicates found, so the last one is deleted.")
            except:
                print("unknown error, but the process will continue")
        else:
            try:
                move(filepath, new_path)
                warnings.warn("duplicate found and placed in the 'duplicates' directory!")
            except:
                move_files(directory, filepath, name, 'exception')
                return None
    elif option == 'exception':
        dir_path = directory + r'\exception'
        new_path = dir_path + r'\{}'.format(name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        try:
            move(filepath, new_path)
            warnings.warn("An exception found and placed in the 'exception' directory!")
        except:
            return None
    elif option == 'scanned':
        dir_path = directory + r'\scanned'
        new_path = dir_path + r'\{}'.format(name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        try:
            move(filepath, new_path)
            warnings.warn("A scanned file found and placed in the 'scanned' directory!")
        except:
            return None


# Function to get the authors' names and publication year using the DOI number
def get_authors_and_year(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    data = json.loads(response.text)
    try:
        authors = data['message']['author']
    except:
        surnames = "unknown"
        authors = "unknown"
    title = data['message']['title'][0]
    try:
        year = data['message']['published']['date-parts'][0][0]
    except:
        year = ""
    surnames = []
    if authors != "unknown":
        for author in authors:
            surname = author["family"]
            surnames.append(surname)
            if len(surnames) > 2:
                surnames[1] = 'et al.'
                surnames.pop(2)
                surnames[0] = temp_surname
                break
            elif len(surnames) == 2:
                temp_surname = surnames[0]
                surnames[0] += ','

    title = re.sub(r'[^\w\s-]+', '', title)
    return surnames, year, title


# Function to rename the PDF file
def rename_file(directory, filepath, title, surnames, year, counter, total_count):
    filename = os.path.basename(filepath)
    new_filename = f"[{' '.join(surnames)} - {year}] {title.replace(':', '')}.pdf"
    if len(new_filename) > 250:
        new_filename = r"{}.pdf".format(new_filename[:250])
    try:
        os.rename(filepath, os.path.join(os.path.dirname(filepath), new_filename))
        print("[{}%] {} is renamed as {}".format(min(round(100 * float(counter) / float(total_count)), 100), filename,
                                                 new_filename))
    except:
        move_files(directory, filepath, new_filename, 'duplicate')
        return None


# Main function to process all PDF files in a directory
def process_original_pdfs(directory):
    total_count = 0
    count = 0
    exception_counter = 0
    scan_counter = 0
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            total_count += 1
    print("{} Files found!".format(total_count))
    for filename in os.listdir(directory):
        count += 1
        if filename.endswith(".pdf"):
            filepath = os.path.join(directory, filename)
            # open the PDF file
            with open(filepath, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                writer = PyPDF2.PdfWriter()
                try:
                    pdf_title = pdf.metadata.title
                except:
                    pdf_title = "Unknown"

                f.close()
            if pdf_title == "Unknown":
                exception_counter += 1
                name = "exception{}.pdf".format(str(exception_counter))
                move_files(directory, filepath, name, 'exception')
                continue
            elif pdf_title[:3] == "doi":
                surnames, year, pdf_title = get_authors_and_year(pdf_title.replace("doi:", ""))
            elif pdf_title.endswith(".qxd"):
                exception_counter += 1
                name = "exception{}.pdf".format(str(exception_counter))
                move_files(directory, filepath, name, 'exception')
                continue
            elif pdf_title.startswith("Scanned") or pdf_title.startswith("scanned"):
                scan_counter += 1
                name = "scanned{}.pdf".format(str(scan_counter))
                move_files(directory, filepath, name, 'scanned')
                continue
            else:
                if get_doi(pdf_title):
                    doi = get_doi(pdf_title)
                    surnames, year, pdf_title = get_authors_and_year(doi)
                else:
                    exception_counter += 1
                    name = "exception{}.pdf".format(str(exception_counter))
                    move_files(directory, filepath, name, 'exception')
                    continue
            rename_file(directory, filepath, pdf_title, surnames, year, count, total_count)


def process_scanned_pdfs(directory, titles):
    total_count = 0
    count = 0
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            total_count += 1
    print("{} Files found!".format(total_count))
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            filepath = os.path.join(directory, filename)
            pdf_title = titles[count]
            pdf_title.replace("ä", "ae").replace("ü", "ue").replace("ß", "ss").replace("Ä", "Ae").replace("Ü", "Ue")
            count += 1
            doi = get_doi(pdf_title)
            surnames, year, pdf_title = get_authors_and_year(doi)
            rename_file(directory, filepath, pdf_title.title(), surnames, year, count, total_count)


def initiation_time(raw_path, opt=None):
    print("\nMake sure that all PDF files are closed. You have 10 seconds to check.")
    text = "10..9..8..7..6..5..4..3..2..1"
    for char in text:
        print(char, end='', flush=True)
        time.sleep(10 / len(text))
    surprise_me(raw_path)
    if opt is None:
        os.system('cls')


# main
def main():
    os.system('cls')
    print('-------------------------------------------------------------------------\n'
          '                        PDF RENAMER for Academia!!                       \n'
          '                            v1.0.4 (March 2023)                          \n'
          '                            Created by uygarkov                          \n'
          '                          www.github.com/uygarkov                        \n'
          '-------------------------------------------------------------------------')
    time.sleep(2)

    scan_or_original = input("Is your PDF scanned or original copy? \n"
                             "S : Scanned\n"
                             "O : Original\n"
                             "[O/S]? ")

    while True:
        user_input = input("Enter the path of your directory: ")
        raw_path = r"{}".format(user_input)
        secured_path = raw_path
        if scan_or_original == 'S':
            titles = list()
            path_to_txt = raw_path + r"\titles.txt"
            time.sleep(2)
            text = "\nPlease make sure that you wrote the titles of articles in the titles.txt in your directory.\n" \
                   "Sequence is important! Example:\n" \
                   "Article Title 1\n" \
                   "Article Title 2\n" \
                   "DONT FORGET TO SAVE THE .TXT DOCUMENT!\n" \
                   "EVERY LINE MUST CONTAIN ONE TITLE, DONT USE 2 LINES FOR ONE ARTICLE!!\n" \
                   "You have 10 seconds if you still did not save the .txt file.\n" \
                   "Please close the PDF files otherwise the program will fail\n"

            for char in text:
                print(char, end='', flush=True)
                time.sleep(10 / len(text))

            initiation_time(raw_path, "S")
            if os.path.exists(path_to_txt):
                os.system('cls')
                print("\nGreat! Reading the .txt file...")
                time.sleep(2)
                print('Process started!')
                time.sleep(2)
                start_time = time.time()
                time.sleep(3)
                with open(path_to_txt, 'r') as txt:
                    for lines in txt:
                        titles.append(lines.rstrip().title())
                    txt.close()
                process_scanned_pdfs(raw_path, titles)
                end_time = time.time()
                print("\nThe all renaming process completed in {} seconds!".format(round(end_time - start_time)))
                print("The program will shutdown in 5 seconds")
                time.sleep(5)
                break

            else:
                time.sleep(3)
                print("\nI could not find any titles.txt file but I created one for you! Once you wrote the titles,\n"
                      "run me again. See you soon!")
                filename = "titles.txt"
                with open(path_to_txt, "w") as f:
                    f.write("CLEAR WHOLE PAGE\n"
                            "Please make sure that you wrote the titles of articles in the titles.txt in your directory.\n"
                            "Sequence is important! Example:\n"
                            "Article Title 1\n"
                            "Article Title 2\n"
                            "CLEAR WHOLE PAGE")
                filepath = os.path.join(path_to_txt, filename)
                time.sleep(3)
                print("\nFile created at:", filepath)
                exit()
        elif scan_or_original == 'O':
            if os.path.exists(user_input):
                print('The file found!\n')
                time.sleep(2)
                initiation_time(raw_path)
                print('Process started!')
                time.sleep(2)
                start_time = time.time()
                process_original_pdfs(raw_path)
                end_time = time.time()
                print("\nThe all renaming process completed in {} seconds!".format(round(end_time - start_time)))
                print("The program will shut down in 5 seconds")
                time.sleep(5)
                break
            else:
                print('The specified file does NOT exist! Make sure that it does not contain any forbidden characters\n'
                      'i.e " , ? * . \ /\n')


if __name__ == '__main__':
    main()

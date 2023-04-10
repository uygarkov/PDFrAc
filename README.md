# PDFrAc (PDF Renamer for Academia!)

## Description

`PDFrAc` is a software that renames the PDF files in the format:

- [{Authors} - {Published Year}] {Title}.pdf

### Example:

- [Kovanci - 2023] My first article.pdf

When the user downloads an article from the journal websites, those PDFs usually have strange names that are assigned by the algorithms. `PDFrAc`, checks the metadata of the PDF and finds its either title or the DOI number. Then it gets all required information of the article using the `CrossRef` library. 
`PDFrAc` also works for scanned articles! However, the user must write the article titles in a .txt file, so `PDFrAc` can read them and find other required information to rename them as well.

## Installation

Simply install using the pip command:

```bash
pip install -i https://test.pypi.org/simple/ uygarkov-PDFrAc==1.0.5
```

Then you can run the code using the command:

```bash
pdfrac
```

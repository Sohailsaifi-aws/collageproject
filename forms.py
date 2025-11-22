class BookForm:
    def __init__(self, form):
        self.title = form.get('title')
        self.author = form.get('author')
        self.isbn = form.get('isbn')
        self.publisher = form.get('publisher')
        self.quantity = form.get('quantity')

    def is_valid(self):
        return self.title and self.author and self.quantity


class IssueForm:
    def __init__(self, form):
        self.student_name = form.get('student_name')
        self.roll_no = form.get('roll_no')
        self.contact = form.get('contact')
        self.book_id = form.get('book_id')

    def is_valid(self):
        return self.roll_no and self.book_id


class ReturnForm:
    def __init__(self, form):
        self.issue_id = form.get('issue_id')

    def is_valid(self):
        return self.issue_id

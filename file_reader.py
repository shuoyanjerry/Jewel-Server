# You need to implement the "get" and "head" functions.
class FileReader:
    def __init__(self):
        pass

    # The server received a GET request for the given `filepath`.
    #
    # The `cookies` argument is a list of binary strings containing each of
    # the cookies sent by the client.
    #
    # This function must return a binary string of the file contents. If the
    # `filepath` does not exist, `None` should be returned.
    def get(self, filepath, cookies=None):
        """
        Returns a binary string of the file contents, or None.
        """
        try:
            with open(filepath, 'rb') as file:
                return file.read()

        except FileNotFoundError:
            return None

        except IsADirectoryError:
            content = "<html><body><h1>{:}</h1></body></html>".format(filepath)
            return content.encode()

    # The server received a HEAD request for the given `filepath`.
    #
    # The `cookies` argument is a list of binary strings containing each of
    # the cookies sent by the client.
    #
    # This function must return the size of the file to be returned in bytes. If the
    # `filepath` does not exist, `None` should be returned.
    def head(self, filepath, cookies=None):
        """
        Returns the size to be returned, or None.
        """
        try:
            with open(filepath, 'rb') as file:
                return len(file.read())

        except FileNotFoundError:
            return None

        except IsADirectoryError:
            content = "<html><body><h1>{:}</h1></body></html>".format(filepath)
            return len(content)


class BookSeries:
    def __init__(self, name, description, order, franchise, reboots, characters, locations, events):
        self.name = name
        self.description = description
        self.order = order
        self.franchise = franchise
        self.reboots = reboots
        self.characters = characters
        self.locations = locations
        self.events = events
        self.books = []
        self.title_requirements = {}

    def add_book(self, book):
        self.books.append(book)

    def remove_book(self, book):
        self.books.remove(book)

    def get_books(self):
        return self.books

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def set_description(self, new_description):
        self.description = new_description

    def get_order(self):
        return self.order

    def set_order(self, new_order):
        self.order = new_order

    def get_franchise(self):
        return self.franchise

    def set_franchise(self, new_franchise):
        self.franchise = new_franchise

    def get_reboots(self):
        return self.reboots

    def add_reboot(self, reboot):
        self.reboots.append(reboot)

    def remove_reboot(self, reboot):
        self.reboots.remove(reboot)

    def get_characters(self):
        return self.characters

    def add_character(self, character):
        self.characters.append(character)

    def remove_character(self, character):
        self.characters.remove(character)

    def get_locations(self):
        return self.locations

    def add_location(self, location):
        self.locations.append(location)

    def remove_location(self, location):
        self.locations.remove(location)

    def get_events(self):
        return self.events

    def add_event(self, event):
        self.events.append(event)

    def remove_event(self, event):
        self.events.remove(event)

    def get_book_count(self):
        return len(self.books)

    def get_title_requirements(self):
        # default title requirements
        self.title_requirements = {
            "genre": "picture book",
            "word_count": 500,
            "audience": "children",
            "alignment_with_series_theme": 0.5,
            "illustration_plates": ["Text Only", "Text and Illustration", "Illustration Only"],
            "illustration_generators": ["Stable Diffusion", "DALL-E 2", "Midjourney"],
            "illustrations": 12
        }
        return self.title_requirements
class Franchise:
    def __init__(self, name, description, order, book_series, characters, locations, events):
        self.name = name
        self.description = description
        self.order = order
        self.book_series = book_series
        self.characters = characters
        self.locations = locations
        self.events = events

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def set_description(self, new_description):
        self.description = new_description

    def get_order(self):
        return self.order

    def set_order(self, new_order):
        self.order = new_order

    def get_book_series(self):
        return self.book_series

    def add_book_series(self, book_series):
        self.book_series.append(book_series)

    def remove_book_series(self, book_series):
        self.book_series.remove(book_series)

    def get_characters(self):
        return self.characters

    def add_character(self, character):
        self.characters.append(character)

    def remove_character(self, character):
        self.characters.remove(character)

    def get_locations(self):
        return self.locations

    def add_location(self, location):
        self.locations.append(location)

    def remove_location(self, location):
        self.locations.remove(location)

    def get_events(self):
        return self.events

    def add_event(self, event):
        self.events.append(event)

    def remove_event(self, event):
        self.events.remove(event)

    def get_book_series_count(self):
        return len(self.book_series)


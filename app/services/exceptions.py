class BookingError(Exception):
    pass


class SlotAlreadyBookedError(BookingError):
    pass


class BookingNotFoundError(BookingError):
    pass

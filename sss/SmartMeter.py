import random


class SmartMeter:
    """
    attributes for Smart Meter class
    ID -- the ID that corresponds to each smart meter
    degree -- the number of aggregators -1, corresponds to degree of polynomial
    secret -- the secret that the smart meter has, updated at each time instance
    polynomial -- the randomly generated polynomial for creating shares
    coeff_list -- the randomly generated coefficients  used to create the polynomial
    shares_list -- holds the shares that this smart meter created
    """

    def __init__(self):
        self.ID = 0
        self.degree = 0
        self.secret = 0
        self.polynomial = ""
        self.coeff_list = []
        self.shares_list = []
        self.times_list = []
        self.zp_space = 0

    def set_zp_space(self, zp):
        self.zp_space=zp


    def set_id(self, ID):
        """
        set the ID var
        :param ID: the ID of the smart meter
        """
        self.ID = ID

    def set_degree(self, deg):
        """
        set the degree variable
        :param deg: the degree of the polynomial
        """
        self.degree = deg

    def set_polynomial(self, poly):
        """
        was used for testing of a predetermined polynomial
        :param poly:  the set polynomial of the smart meter
        """
        self.polynomial = poly

    def set_coeff_list(self, coeff_list):
        """
        was used for testing of a predetermined polynomial
        :param coeff_list: the coefficients of the polynomial
        """

        self.coeff_list = coeff_list

    def get_ID(self):
        """
        :return:  the ID of this smart meter
        """
        return self.ID

    def get_polynomial(self):
        """
        :return: the polynomial of this smart meter
        """
        return self.polynomial

    def set_secret(self, secret):
        """
        was used for a predetermined secret for testing purposes
        :param secret: the secret of the smart meter
        """
        self.secret = secret

    def create_polynomial(self, max_coeff):
        """
        function to create a polynomial at each time instance for a smart meter
        creates a random string of bits to determine the powers of x in the polynomial
        then generates a random integer as the coefficient for the bits that are 1s
        appends the secret to the end of the coefficient
        """
        self.coeff_list = []
        bit_string = [1]
        # loop over the range of the degree to generate whether the power of x will be present
        for i in range(1, self.degree):
            bit = random.randint(0, 1)
            bit_string.append(bit)
        power = self.degree
        polystring = ""

        # loop over the binary string and generate the coefficients
        for i in range(0, len(bit_string)):
            if bit_string[i] == 1:
                coeff = random.randint(1, max_coeff)
                polystring += str(coeff) + "x^" + str(power) + "+"
                self.coeff_list.append(coeff)
            else:
                self.coeff_list.append(0)
            power -= 1

        # add the secret to the end of the polynomial as the constant
        polystring += str(self.secret)
        self.polynomial = polystring
        print(self.polynomial)

    def create_shares(self, aggregator_ID):
        """
        generates the shares from this smart meter
        using the polynomial that belongs to this smart meter the ID value of the aggregator that is passed in
        is plugged in for the x value and the share is the total of the polynomial
        appends the share value to the aggregator list and to the smart meter list
        :param aggregator: the aggregator that this share is being sent to
        """
        length = len(self.coeff_list)
        power = self.degree
        value = 0
        for i in range(0, length):
            value += self.coeff_list[i] * (aggregator_ID ** power)
            power -= 1
        value += self.secret
        self.shares_list.append(value)
        return value

    def get_shares_list(self):
        """
        return the shares list as a string
        :return: the list of shares
        """
        return str(self.shares_list)

    def add_time(self, value):
        """
        append the length of time it took to send a share to the list
        :param value: the time it took to send the share
        """
        self.times_list.append(value)

    def get_time(self):
        """
        print the list of times
        """
        print(self.times_list)

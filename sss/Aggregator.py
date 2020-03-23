__author__ = "Claire Casalnova"



class Aggregator:
    """
    Aggregator class attributes
    ID -- the ID that corresponds to the aggregators
    shares_list -- the list of shares that the smart meters send to the aggregator
        gets added to as more shares come from the same smart meters
    total -- the total of all the shares added together
    current_total -- the total of the most recent shares
    delta_func_multiplier -- the delta function multiplier which is made using lagrange interpolation
    """

    def __init__(self, ID, num_smart_meters):
        self.ID = ID
        self.billing_dict = dict()
        self.num_sm = num_smart_meters
        for i in range(1, num_smart_meters+1):
            self.billing_dict[i] = 0
        self.spatial_counter = 0

        self.bill_results = [0] * num_smart_meters
        self.shares_list = 0
        self.current_total = 0
        self.total = 0
        self.delta_func_multiplier = 0
        self.lagrange = ""
        self.sumofshares= 0
        self.time = 0

    def update_billing_counters(self,value,meter_id):
        self.billing_dict[meter_id] = value
        print(self.billing_dict)

    def update_spatial_counter(self,value):
        self.spatial_counter += value

    def get_spatial_total(self):
        return self.spatial_counter

    def reset_spatial(self):
        self.spatial_counter = 0

    def get_billing_amount(self, num):
        amount = 0
        # mult = int(self.calc_billing_lagrange(num))
        print("num:", num)
        mult = self.delta_func_multiplier
        print("mult: ", mult)
        print(self.billing_dict[num])
        amount += mult * int(self.billing_dict[num])
        print("billing amount", amount)
        return int(amount)

    def calculate_delta(self,zp=0):
        return int(self.spatial_counter * self.delta_func_multiplier)

    def set_lagrange(self, equation):
        self.lagrange = equation

    def calc_billing_lagrange(self, num):
        top = 1
        bottom = 1
        for i in range(1, self.num_sm + 1):
            if i != num:
                top *= -i
                bottom *= (num - i)
        return top / bottom

    def calculate_lagrange_multiplier(self, num_aggregators):
        """
        utilizes the idea of lagrange interpolation to create a multiplier for the recreation of the secrets
        :param num_aggregators: the total number of aggregators that are in the system
        """
        top = 1
        bottom = 1
        for i in range(1, num_aggregators + 1):
            if i != self.get_ID():
                top *= -i
                bottom *= (self.get_ID() - i)
        self.delta_func_multiplier = top / bottom



    def get_ID(self):
        """
        :return: the ID of the aggregator
        """
        return self.ID



    def get_current_total(self):
        """
        :return: the current total of the shares that were most recently sent
        """
        return self.current_total

    def get_lagrange_multiplier(self):
        """
        :return: the lagrange multiplier
        """
        return self.delta_func_multiplier

    def append_shares(self, share):
        """
        put the share value in the correct location corresponding to the smart meter id
        :param share: the share that was sent
        :param sm_id: the id of the smart meter
        """
        self.shares_list += share

    def calc_sum(self, value):
        """
        calculate the sum of the shares that were sent by adding the value
        :param value: the value that corresponds to the share multiplied by the delta func multiplier of the agg
        :param sm_id: the smart meter id
        """
        self.sumofshares += value

    def get_sum(self):
        """
        return the sum of the shares based on the passed smart meter id
        :param sm_id: the id of the smart meter
        :return: the sum of the shares
        """
        return self.current_total

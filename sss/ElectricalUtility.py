__author__ = "Claire Casalnova"

class ElectricalUtility:
    """
    class for the electrical utility company
    includes a list of the values that the EU is sent at each time instance
    these values are comprised of the total of the secrets from the smart meters
    """

    def __init__(self):
        """
        values- corresponds to the readings from specified smart meters
        num_aggregators - the number of aggregators in the network
        smart_meter_num - the number of smart meters in the network
        """
        self.spatial_sum = 0
        self.num_aggregators = 0
        self.smart_meter_num = 0
        self.price_per_unit = 10
        self.aggregators = []
        self.bills = []

    def set_spatial_sum(self, value):
        self.spatial_sum += value

    def get_spatial_sum(self):
        return self.spatial_sum

    def generate_bill(self, smart_meter, amount):
        print("sm:", smart_meter, "a:",amount)
        print("bill:", self.bills[smart_meter-1])
        self.bills[smart_meter-1] += amount



    def set_num_aggs(self, num):
        """
        sets the num_aggregators in the network
        :param num: the number of aggs
        """
        self.num_aggregators = num

    def get_num_aggs(self):
        return self.num_aggregators

    def set_num_sm(self, num):
        """
        set the number of smart meters var and create the values array to be that length
        :param num: number of smart meters
        """
        self.smart_meter_num = num
        self.bills = [0] * self.smart_meter_num

    def get_total_amount(self):
        for i in range(0,len(self.bills)):
            self.bills[i]=self.bills[i]*self.price_per_unit

    def get_bills(self):
        return self.bills

# -*- coding: utf-8 -*-
import logging
import json
import pandas as pd
from flask import Flask, jsonify, make_response, request
from cost_functions import process

app = Flask(__name__)


class Webhook:
    def __init__(self):
        self.parameters = ['District', 'Name', 'Street', 'Date', 'Discount', 'Rooms', 'TotalArea', 'PPSM', 'TotalPrice',
                           'Parameters', 'Type']
        self.parameter_values = {p: '' for p in self.parameters}
        self.cost_coefficients = {'Location': 5, 'Date': 1, 'District': 4, 'Rooms': 2, 'TotalArea': 2,
                                 'PPSM': 2, 'TotalPrice': 2, 'Type': 1}

    def get_parameter_values(self, obj):
        for parameter in self.parameters:
            contexts = obj['result']['contexts']
            input_parameters = obj['result']['parameters']
            for context in contexts:
                if parameter in context['parameters'] and len(context['parameters'][parameter]) > 0:
                    self.parameter_values[parameter] = context['parameters'][parameter]
            if parameter in input_parameters and len(input_parameters[parameter]) > 0:
                self.parameter_values[parameter] = input_parameters[parameter]

    def get_known_parameter_values(self):
        known_parameters = []
        for parameter in self.parameters:
            if self.parameter_values[parameter] != '':
                known_parameters.append(parameter)
        return known_parameters

    def compose_telegram_card_response(self, text, names, urls):
        data = {
            'telegram':
                {
                    'text': text,
                    'reply_markup': {
                        'inline_keyboard': [
                            [{'text': n, 'url': u}] for n, u in zip(names, urls)
                        ]
                    }
                }
        }
        result = {'source': 'webhookdata', 'data': data}
        return result

    def search_for_parameter(self, parameter):
        if self.parameter_values['Type'] == '':
            self.parameter_values['Type'] = 'flat'
        text_response = ''
        search_table = pd.read_csv('FullDB.csv', dtype='str').fillna('-2')
        search_table = search_table[(search_table['Name'] == self.parameter_values['Name']) &
                                    (search_table['Type'] == self.parameter_values['Type'])]
        temp = pd.DataFrame()
        temp['Name'] = search_table['Name'] + ' (' + search_table['Rooms'] + ')'
        temp[parameter] = search_table[parameter]
        search_table = temp
        search_table = search_table.drop_duplicates()
        for name, parameter_value in zip(search_table['Name'], search_table[parameter]):
            text_response += str(name) + ': ' + str(parameter_value) + '\n'
        return {'speech': text_response, 'displayText': text_response, 'source': 'webhookdata'}

    def search_for_complex(self, parameters):
        if self.parameter_values['Type'] == '':
            self.parameter_values['Type'] = 'flat'
            parameters.append('Type')
        search_table = pd.read_csv('FullDB.csv', dtype='str')
        search_table['URL'] = search_table['URL'].fillna('https://kmb.ua/')
        search_table = search_table.fillna('-1')
        try:
            parameters.remove('Parameters')
        except Exception:
            pass
        distance = [0 for _ in range(search_table.shape[0])]
        for parameter in parameters:
            distance += process(self.parameter_values[parameter], parameter)/float(self.cost_coefficients[parameter])
        search_table['Distance'] = pd.Series(distance)
        search_table = search_table[search_table['Name'] != '-1']
        if search_table[search_table['Distance'] == 0].shape[0] >= 10:
            search_table = search_table[search_table['Distance'] == 0]
        else:
            search_table = search_table.sort_values(by=['Distance']).reset_index()[:10]
        filters = parameters
        filters.append('Name')
        filters.append('URL')
        search_table = search_table.filter(filters)
        search_table = search_table.drop_duplicates().reset_index()
        names = []
        for name, _ in zip(search_table['Name'], range(search_table['Name'].size)):
            name += ': '
            for parameter in parameters:
                if parameter in ['Name', 'Type', 'URL']:
                    continue
                name += search_table[parameter][_] + '; '
            names.append(name)
        search_table['Name'] = pd.Series(names)
        if search_table.shape[0] > 0 and len(parameters) > 1:
            text_response = 'По вашему запросу найдены такие комплексы: '
            return self.compose_telegram_card_response(text_response, search_table['Name'], search_table['URL'])
        else:
            text_response = 'По вашему запросу ничего не найдено.'
            return {'speech': text_response, 'displayText': text_response, 'source': 'webhookdata'}

    def get_result(self, obj):
        result = {}
        self.get_parameter_values(obj)
        action_name = str(obj['result']['action'])
        if action_name == 'search_for_parameter':
            if self.parameter_values['Name'] != '':
                result = self.search_for_parameter(self.parameter_values['Parameters'])
        if action_name == 'search_complex':
            complex_parameters = self.get_known_parameter_values()
            if len(complex_parameters) > 0:
                result = self.search_for_complex(complex_parameters)
            else:
                text_response = 'Введён запрос поиска без параметров или же по запросу ничего не найдено...'
                result = {'speech': text_response, 'displayText': text_response, 'source': 'webhookdata'}
        result['contextOut'] = obj['result']['contexts']
        return result


@app.route('/', methods=['POST'])
def post():
    wb = Webhook()
    req = request.get_json(silent=True, force=True)
    res = wb.get_result(req)
    return make_response(jsonify(res))


if __name__ == '__main__':
    file = open('sample_request.json', 'r')
    j = json.load(file)
    print(app.test_client().post('/', data=json.dumps(j)))
# [END app]

import json
import subprocess
import datetime
import re
import sys
import os


params = sys.argv
flag_file = 'path_file'.upper()
flag_dir = 'path_dir'.upper()
request_list = ['OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'TRACE', 'CONNECT']
access_expansion = ['log', 'txt']
default_access_expansion = 'log'
file_or_path = [flag_file, flag_dir]
acces_side = ['left', 'right']

def check_params(params):
    file_expansion = ''
    if len(params) > 3:
        raise Exception( f"Ошибка. Слишком много аргументов." )
    if len(params) < 2:
        raise Exception( f"Ошибка. Передайте путь до фала или дирректории." )
    if len(params) == 3:
        try:
            if params[2] not in access_expansion:
                file_expansion = default_access_expansion
            else:
                file_expansion = params[2]
        except Exception as e:
            file_expansion = default_access_expansion
    try:
        check_f = os.path.isfile(params[1])
        check_d = os.path.isdir(params[1])
        if check_f == False and check_d == False:
            raise Exception( f"Ошибка. Переданный путь не является файлом или дирректорией!" )
        if check_f == False:
            return flag_dir, file_expansion, params[1]
        else:
            return flag_file, file_expansion, params[1]
    except Exception as e:
        raise


def parse_log(flag, path, file_expansion):
    if str(flag).upper() not in file_or_path:
        raise Exception(f"Ошибка. Не удалось определить чем является переданный параметр.")

    booklogs = ''
    if flag == flag_dir:
        access_log_files = []
        file_id_dir = subprocess.check_output( ('ls', str(path) ), encoding='UTF-8' )
        file_id_dir = file_id_dir.split('\n')[:-1]
        for suitable_name in file_id_dir:
            if re.search( fr'({file_expansion})\.[0-9]+$', suitable_name ) or re.search( fr'\.{file_expansion}$', suitable_name ):
                access_log_files.append(suitable_name)
        for file_name in access_log_files:
            read_logs = subprocess.check_output( ( 'cat', path + file_name), encoding='UTF-8' )
            booklogs += read_logs
    if flag == flag_file:
        if re.search( fr'({file_expansion})\.[0-9]+$', path ) or re.search( fr'\.{file_expansion}$', path ):
            read_logs = subprocess.check_output( ( 'cat', path ), encoding='UTF-8' )
            booklogs += read_logs
    booklogs = booklogs.split('\n')[:-1]
    return booklogs

def http_requests(booklogs):
    # Сбор количества запросов по методам и сложение их общего количества
    counter_requests_at_type = {}
    total_request = 0
    counter = 0
    if len(booklogs) == 0:
        raise Exception('Нет строк для обработки!')
    try:
        if booklogs[0] == '' and len(booklogs) == 1:
            raise Exception('Файл пуст!')
    except:
        pass

    for method in request_list:
        for request in booklogs:
            if request == '':
                pass
            else:
                status_code = re.findall( fr'\"{method}', request )
                if status_code == []:
                    pass
                else:
                    counter += 1
                    counter_requests_at_type[method] = counter
        total_request += counter
        counter = 0
    rezult_counter_requests = ''
    for item in counter_requests_at_type:
        rezult_counter_requests += item + '-' + str(counter_requests_at_type[item]) + ','
    rezult_counter_requests = rezult_counter_requests[:-1]
    return {'rezult_total_request': total_request, 'rezult_counter_requests' : rezult_counter_requests}

def often_request(booklogs):
    # Самые частые запросы с IP
    list_ip = []
    res_often_request = {}
    for item in booklogs:
        res = re.findall( r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', item )
        if len(res) != 0:
            list_ip.append(res[0])
    uniq_id = set(list_ip)
    counter_id = 0
    for uip in uniq_id:
        for ip in list_ip:
            if uip == ip:
                counter_id += 1
                res_often_request[uip] = counter_id
        counter_id = 0
    tmp_list = []
    for i in res_often_request:
        tmp_list.append(res_often_request[i])
    tmp_list.sort()
    tmp_list.reverse()
    answer_ofter_request = {}
    for big_number in tmp_list[0:3]:
        for ip in res_often_request:
            if res_often_request[ip] == big_number:
                answer_ofter_request[ip] = big_number
    rezult_answer_ofter_request = ''
    for item in answer_ofter_request:
        rezult_answer_ofter_request += item + '-' + str(answer_ofter_request[item]) + ','
    rezult_answer_ofter_request = rezult_answer_ofter_request[:-1]
    return rezult_answer_ofter_request

def create_json_from_string(item, variable_separator, value_separator, key_side):
    if key_side not in acces_side:
        raise Exception( f"Ошибка. Могу принимать только только 'left' или 'right'." )
    item = str(item).split(variable_separator)
    res_json = {}
    counter = 0
    for i in item:
        item[counter] = i.split(value_separator)
        counter += 1
    for n in item:
        if key_side == 'left':
            res_json[n[0]] = n[1]
        else:
            res_json[n[1]] = n[2]
    return res_json

def main():
    flag, expansion, path = check_params( params = params )
    booklogs = parse_log( flag = flag, path = path, file_expansion = expansion )
    http = http_requests(booklogs)
    often_req = often_request(booklogs)
    print('Общее количество запросов: ', str(http['rezult_total_request']))
    print('Количество запросов по HTTP-методам: ', http['rezult_counter_requests'])
    print('Три наиболее частых запросов с IP: ', often_req)

    anwer_json = {
        'total_request' : http['rezult_total_request'] ,
        'counter_requests_by_method' :create_json_from_string(http['rezult_counter_requests'],variable_separator= ',', value_separator = '-', key_side = 'left' ) ,
        'quantity_request_by_ip' : create_json_from_string(often_req,variable_separator= ',', value_separator = '-', key_side = 'left' ),
    }
    current_time = datetime.datetime.now()
    current_time = current_time.ctime()
    current_time = current_time.replace(' ', '-')
    current_time = current_time.replace(':', '-')
    file_name = current_time + '-' + 'result.json'
    with open(file_name, 'w') as file:
        json.dump(anwer_json, file, indent=4, ensure_ascii=False)
    print( anwer_json )

if __name__ == '__main__':
    main()
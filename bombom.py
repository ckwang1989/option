# http://www.liujiangblog.com/course/python/82
# 20190902 future work
# analysis_statement當做基本面filter
# 將通過analysis_statement當做基本面filter的股票下載yahoo finance的.csv
# 再算get_supporting_point
# 繼續把皓謙講的做完

# https://github.com/dsmbgu8/image_annotate.py/issues/4
# echo "backend: TkAgg" >> ~/.matplotlib/matplotlibrc

import sys
#sys.path.insert(0, '/home/ckwang/.local/lib/python2.7/site-packages')
#sys.path.insert(0, '/usr/local/lib/python3.5/dist-packages')
import copy
import argparse
import multiprocessing
from multiprocessing import Process
from multiprocessing import queues
import time
import pickle
import os

from pandas_datareader import data as pdr
import matplotlib.pyplot as plt
#import fix_yahoo_finance as yf
import datetime

import finviz
import copy
import requests
import pandas as pd
#print (finviz.get_stock('AMD'))
#assert False
# Optionable
# Avg Volume
# EPS (ttm)
# EPS next Y
# EPS next Q
# EPS this Y
# EPS next 5Y
# EPS past 5Y
# EPS Q/Q
# 

#assert False

# self.ma_days = 200
# stock_dict = {	supported_point: [{  Interval: xxx 
#										vol_val: xxx	}, {...}, {...}],

#					topk_vol:		[0, 0, top1_volume, 0, 0, 0, top2_volume.....],

#					moving_average: {'2012-02-14': {'type': big_cow,
#													'close': xxx,
#													'MA5': xxx,
#													'MA20': xxx,
#													'MA40': xxx,
#													'MA80': xxx },
#									'2012-02-1X': {'type': small_bear,
#													'close': xxx,
#													'MA5': xxx,
#													'MA20': xxx,
#													'MA40': xxx,
#													'MA80': xxx },
#									....}
#				}

class Trader(object):
	def __init__(self, period_days, difference_rate, stock_folder_path, roe_ttm):
		self.stock_name = -1
		self.period_days = period_days
		self.difference_rate = 0.05#difference_rate
		self.roe_ttm = roe_ttm
		self.stock_folder_path = stock_folder_path
		self.value_group = -1
		self.top_volume_num = 10
		self.part_num = 100
		self.ma_days = 200
		self.nKD = 9

#

	def get_supporting_point(self, stock_name, file_path):
		print ('stock_name: {}'.format(stock_name))
		stock_dict_sum = {'topk_vol':[],'supported_point':{},'moving_average':{}, 'MA_state_dict':{}}
		#stock_dict_sum = {'moving_average':{}}
		stock_dict = {}
		stock_close_list = []
		stock_low_list = []
		stock_high_list = []
		press_list = []
		stock_date_list = []
		stock_volume_list = []
		count = 0
		interval_value_point = 5
		Open_last, High_last, Low_last, Close_last, Volume_last = 0, 0, 0, 0, 0
		with open(file_path, 'r') as file_read:
			for line in file_read.readlines():
				count+=1
				#if count < 12085 or count > 12095:#or count > 13500:
				#	continue
				line = line.split(',')
				if line[0] == 'Date':
					continue
				Date, Open, High, Low, Close, Adj_Close, Volume = line[0], line[1], line[2], line[3], line[4], line[5], (line[6].strip('\n'))
				#print (Open, Volume)
				if Open == 'null' or High == 'null' or Low == 'null' or Close == 'null' or Volume == 'null':
					Open, High, Low, Close, Volume = Open_last, High_last, Low_last, Close_last, Volume_last
				stock_dict[Date] = {'Date': Date,
									'Open': Open,
									'High': High,
									'Low': Low,
									'Close': float(Close),
									'Adj_Close': Adj_Close,
									'Volume': int(Volume)}
				stock_close_list.append(float(Close))
				stock_low_list.append(float(Low))
				stock_high_list.append(float(High))
				stock_volume_list.append(int(Volume))
				stock_date_list.append(Date)
				Open_last, High_last, Low_last, Close_last, Volume_last = Open, High, Low, Close, Volume
		self.interval_value = round(max(stock_close_list) / self.part_num, interval_value_point)
		#print (stock_dict)
		#print (stock_name, 'get_supporting_point')
		topk_volume_list = [0]*self.part_num
		for key in stock_dict_sum.keys():
			if key == 'KD':
				for idx in range(len(stock_close_list)-self.ma_days, len(stock_close_list)):
					n_stock_low = min(stock_low_list[idx-self.nKD+1:idx+1])
					n_stock_high = max(stock_low_list[idx-self.nKD+1:idx+1])
					close = stock_close_list[idx]
					RSV = 100 * ((close-n_stock_low)/(close-n_stock_high))
					# 1 2 3 4 5 6 7 8 len=8 [3:8]->[idx-ma+1:idx+1]
					MA5 = round(sum(stock_close_list[idx-5+1:idx+1]) / 5.0, 2)
					MA20 = round(sum(stock_close_list[idx-20+1:idx+1]) / 20.0, 2)
					MA40 = round(sum(stock_close_list[idx-40+1:idx+1]) / 40.0, 2)
					MA80 = round(sum(stock_close_list[idx-80+1:idx+1]) / 80.0, 2)

			if key == 'topk_vol':
				# topk volume
				#topk_volume_list = [0]*self.part_num
				stock_volume_list_tmp = copy.deepcopy(stock_volume_list)

				for num in range(self.top_volume_num):
					max_volume = max(stock_volume_list_tmp)
					stock_volume_list_tmp.remove(max_volume)
					max_idx = stock_volume_list.index(max_volume)
					max_date = stock_date_list[max_idx]
					max_volume_close = stock_close_list[max_idx]
					#topk_volume_list.append({max_date: {'volume': max_volume, \
					#									'close': max_volume_close}})
					#print (int(max_volume_close//(max_volume_close // self.part_num)))
					idx_tmp = int(max_volume_close/(self.interval_value)) if int(max_volume_close/(self.interval_value)) <= len(topk_volume_list)-1 else len(topk_volume_list)-1
					topk_volume_list[idx_tmp] += max_volume
				#print (topk_volume_list)

				stock_dict_sum['topk_vol'] = topk_volume_list
			if key == 'press':
				# press
				for idx, Close in enumerate(stock_close_list):
					if idx < self.period_days or idx+self.period_days > len(stock_close_list):
						continue
					Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
					if not Close > Close_five_days_pass_min*1.1:
						continue
					Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
					if not Close > Close_five_days_pass_max:
						continue
					Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close > Close_five_days_next_max:
						continue
					Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close > Close_five_days_next_min*1.1:
						continue
					#print (idx, Close)
					press_dict = {'Date': stock_date_list[idx],
									'Volume_Value': Close*stock_dict[stock_date_list[idx]]['Volume'],
									'Close': Close}
					press_list.append(press_dict)
				#print (press_list)
			if key == 'pressed_point':
				press_list = []
				# calculate supported point
				for idx, Close in enumerate(stock_close_list):
					if idx < self.period_days or idx+self.period_days > len(stock_close_list):
						continue

					Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
					if not Close > Close_five_days_pass_min*1.1:
						continue
					Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
					if not Close > Close_five_days_pass_max:
						continue
					Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close > Close_five_days_next_max:
						continue
					Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close > Close_five_days_next_min*1.1:
						continue
					#print (idx, Close)
					press_dict = {'Date': stock_date_list[idx],
									'Volume_Value': Close*stock_dict[stock_date_list[idx]]['Volume'],
									'Volume': stock_dict[stock_date_list[idx]]['Volume'],
									'Close': Close}
					press_list.append(press_dict)

				# interval
				Volume_Value_max = -1
				Volume_max = -1
				press_all_dict = {}
				topk_volume_all_dict = {}
				for num in range(self.part_num):
					press_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] = 0
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] = 0
				

				for press_dict_tmp in press_list:
					num = int(press_dict_tmp['Close'] / self.interval_value)
					press_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] \
						+=press_dict_tmp['Volume_Value']
				# normalize press_all_dict
				# first, get Volume_Value_max
				for press_dict_val in press_all_dict.values():
					Volume_Value_max = press_dict_val if press_dict_val > Volume_Value_max else Volume_Value_max
				# second, normalization
				for press_dict_key in press_all_dict.keys():
					press_all_dict[press_dict_key] = press_all_dict[press_dict_key] / float(Volume_Value_max)


				for idx, value in enumerate(topk_volume_list):
					Volume_max = value if value > Volume_max else Volume_max
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] \
						+=value
				for idx, value  in enumerate(topk_volume_list):
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] \
						= topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] / float(Volume_max)

				press_all_list = []

				for key in topk_volume_all_dict.keys():
					if press_all_list == []:
						press_all_list.append({'Interval': key, \
												'Volume_Value': press_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
					else:
						insert_idx = 0
						for press_dict in press_all_list:
							# 現在要加入的press_all_dict[key]要加到idx多少
							if press_dict['topk_volume'] >= topk_volume_all_dict[key]:
								insert_idx += 1
							else:
								break
						press_all_list.insert(insert_idx, {'Interval': key, \
												'Volume_Value': press_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
#												'''
				#print (press_all_list)
				stock_dict_sum['pressed_point'] = press_all_list


			if key == 'supported_point':
				support_list = []
				# calculate supported point
				for idx, Close in enumerate(stock_close_list):
					if idx < self.period_days or idx+self.period_days > len(stock_close_list):
						continue

					Close_five_days_pass_min = min(stock_close_list[idx-self.period_days:idx])
					if not Close < Close_five_days_pass_min:
						continue
					Close_five_days_pass_max = max(stock_close_list[idx-self.period_days:idx])
					if not Close < Close_five_days_pass_max:
						continue
					Close_five_days_next_max = max(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close < Close_five_days_next_max*1.1:
						continue
					Close_five_days_next_min = min(stock_close_list[idx+1:idx+1+self.period_days])
					if not Close < Close_five_days_next_min:
						continue
					#print (idx, Close)
					support_dict = {'Date': stock_date_list[idx],
									'Volume_Value': Close*stock_dict[stock_date_list[idx]]['Volume'],
									'Volume': stock_dict[stock_date_list[idx]]['Volume'],
									'Close': Close}
					#Volume_Value_max = Close*stock_dict[stock_date_list[idx]]['Volume'] if Close*stock_dict[stock_date_list[idx]]['Volume'] > Volume_Value_max else Volume_Value_max
					#Volume_max = stock_dict[stock_date_list[idx]]['Volume'] if stock_dict[stock_date_list[idx]]['Volume'] > Volume_max else Volume_max
					support_list.append(support_dict)

				# interval
				Volume_Value_max = -1
				Volume_max = -1
				support_all_dict = {}
				topk_volume_all_dict = {}
				for num in range(self.part_num):
					support_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] = 0
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] = 0
				

				for support_dict_tmp in support_list:
					num = int(support_dict_tmp['Close'] / self.interval_value)
					support_all_dict['{}_{}'.format(round(self.interval_value*num, interval_value_point), round(self.interval_value*(num+1), interval_value_point))] \
						+=support_dict_tmp['Volume_Value']
				# normalize support_all_dict
				# first, get Volume_Value_max
				for support_dict_val in support_all_dict.values():
					Volume_Value_max = support_dict_val if support_dict_val > Volume_Value_max else Volume_Value_max
				# second, normalization
				for support_dict_key in support_all_dict.keys():
					support_all_dict[support_dict_key] = support_all_dict[support_dict_key] / float(Volume_Value_max)


				for idx, value in enumerate(topk_volume_list):
					Volume_max = value if value > Volume_max else Volume_max
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] \
						+=value
				for idx, value  in enumerate(topk_volume_list):
					topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] \
						= topk_volume_all_dict['{}_{}'.format(round(self.interval_value*idx, interval_value_point), round(self.interval_value*(idx+1), interval_value_point))] / float(Volume_max)


				# sort by interval value
				'''
				support_all_list = []
				for key in topk_volume_all_dict.keys():
					support_all_list.append({'Interval': key, \
												'Volume_Value': support_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
												'''

				# sort by topk_volume or Volume_Value
#				'''
				support_all_list = []

				for key in topk_volume_all_dict.keys():
					#if support_all_dict[key] == 0:
					#	continue
					if support_all_list == []:
						support_all_list.append({'Interval': key, \
												'Volume_Value': support_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
					else:
						insert_idx = 0
						for support_dict in support_all_list:
							# sorted by supported volume * close value
							#if support_dict['Volume_Value'] >= support_all_dict[key]:
							# sorted by topk volume
							# 現在要加入的support_all_dict[key]要加到idx多少
							if support_dict['topk_volume'] >= topk_volume_all_dict[key]:
								insert_idx += 1
							else:
								break
						support_all_list.insert(insert_idx, {'Interval': key, \
												'Volume_Value': support_all_dict[key], \
												'topk_volume': topk_volume_all_dict[key]})
#												'''
				#print (support_all_list)
				stock_dict_sum['supported_point'] = support_all_list

			if key == 'moving_average':
#					moving_average: {'2012-02-14': {'type': big_cow,
#													'close': xxx,
#													'MA5': xxx,
#													'MA20': xxx,
#													'MA40': xxx,
#													'MA80': xxx },
#									'2012-02-1X': {'type': small_bear,
#													'close': xxx,
#													'MA5': xxx,
#													'MA20': xxx,
#													'MA40': xxx,
#													'MA80': xxx },
#									....}
				MA_dict = {}
				MA_dict_all = {}
				MA_state_dict = {}
				first_enter = True
				MA40_state = 0
				MA80_state = 0
				change_state = False
				MA40_change_state, MA80_change_state = False, False
				for idx in range(len(stock_close_list)-1, len(stock_close_list)-self.ma_days, -1):
					#print (len(stock_close_list)-1, len(stock_close_list)-self.ma_days, -1)
					#print (idx)
					close = stock_close_list[idx]
					# 1 2 3 4 5 6 7 8 len=8 [3:8]->[idx-ma+1:idx+1]
					MA5 = round(sum(stock_close_list[idx-5+1:idx+1]) / 5.0, 2)
					MA20 = round(sum(stock_close_list[idx-20+1:idx+1]) / 20.0, 2)
					MA40 = round(sum(stock_close_list[idx-40+1:idx+1]) / 40.0, 2)
					MA80 = round(sum(stock_close_list[idx-80+1:idx+1]) / 80.0, 2)
					#print (MA5, MA20, MA40, MA80)
					situation_type = 'big_cow' if MA5 > MA20 > MA40 > MA80 else 'small_cow' if MA40 > MA80 \
									else 'big_bear' if MA5 < MA20 < MA40 < MA80 else 'small_bear'
					MA_dict = {'situation_type': situation_type, \
								'close': close, \
								'MA5': MA5, \
								'MA20': MA20, \
								'MA40': MA40, \
								'MA80': MA80 }
					MA_dict_all['{}'.format(stock_date_list[idx])] = MA_dict
					
					

					if first_enter:
						first_enter = False
					else:
						MA40_state = 1 if MA40 > MA40_last else -1
						MA80_state = 1 if MA80 > MA80_last else -1
						if MA_state_dict == {}:
							MA_state_dict = {'MA40_state_keep': 0, 'MA80_state_keep': 0}

						else:
							MA40_change_state = False if ((MA40_state_last == MA40_state) and (MA40_change_state == False)) else True
							MA80_change_state = False if ((MA80_state_last == MA80_state) and (MA80_change_state == False)) else True
							if not MA40_change_state:
								MA_state_dict['MA40_state_keep'] += 1
							else:
								MA40_change_state = True

							if not MA80_change_state:
								MA_state_dict['MA80_state_keep'] += 1
							else:
								MA80_change_state = True
						#try:
						#	print (MA40, MA40_last, MA40_state, MA40_state_last, MA40_change_state)
						#	print (MA80, MA80_last, MA80_state, MA80_state_last, MA80_change_state)
						#	print ((MA40_state_last == MA40_state), (MA40_change_state == False))
						#	input('wait')
						#except:
						#	pass
						MA40_state_last = MA40_state
						MA80_state_last = MA80_state

					MA40_last, MA80_last, = MA40, MA80



				#print (MA_dict_all)
				stock_dict_sum['moving_average'] = MA_dict_all
				stock_dict_sum['MA_state_dict'] = MA_state_dict

		print (stock_dict_sum)
				


# 用基本面篩選
# MA 40 80負斜率持續 70天就不要
# 判斷大小牛熊（大牛：MA5>MA20>MA40>MA80、小牛：MA40>MA80）
#  

# csv_type： MA_5 MA_20 MA_40 MA_80 MA_sum 支撐 大量

		# 將value_volume=0的刪除
		# 用將value_volume排序，由大到小
		# 找到前10大量的落點
		# 回測改變period_days、difference_rate、要幾個最大量、
		# 找到support point時抓前後幾天、top k是volume or volume*value的detection rate
		

		#count_list = range(len(stock_date_list))
		#plt.plot(count_list, stock_volume_list)
		#plt.show()


		"""
		import numpy as np
		import pandas as pd
		import matplotlib.pyplot as plt

		x = stock_date_list
		x = np.asarray(range(len(stock_date_list)))
		y_val = np.asarray(stock_close_list)*2000000
		y_vol = np.asarray(stock_volume_list)
		print (x)
		print (y_val)
		plt.plot(x, y_val)
		plt.plot(x, y_vol)
		plt.show()
		"""

#		fig, axes = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(8, 8))
#		labelled_data = zip((y_val, y_vol), ('value', 'volume'), ('b', 'g'))
#		fig.suptitle('Three Random Trends', fontsize=16)
#
#		for i, ld in enumerate(labelled_data):
#			ax = axes[i]
#			ax.plot(x, ld[0], label=ld[1], color=ld[2])
#			#ax.set_ylabel('Cum. sum')
#			#ax.legend(loc='upper left', framealpha=0.5, prop={'size': 'small'})
#		axes[-1].set_xlabel('Date')
#		plt.show()

	def analysis_statement(self, stock_name):
		stock_dict = finviz.get_stock(stock_name)
		if not stock_dict['Optionable'] == 'Yes':
			#print ('unOptionable')
			return False
		if not 'M' in stock_dict['Avg Volume']:
			#print ('low Volume')
			return False
		if '-' in stock_dict['ROE']:
			#print ('-roe')
			return False
		if float(stock_dict['ROE'][:-1]) < 10.0:
			#print ('roe')
			return False
		if '-' in stock_dict['EPS Q/Q']:
			#print (stock_name, 'EPS Q/Q')
			#print ('eps')
			return False
		if '-' in stock_dict['EPS next Q']:
			#print (stock_name, 'EPS next Q')
			#print ('eps2')
			return False
		if '-' in stock_dict['Sales Q/Q']:
			#print (stock_name, 'EPS next Q')
			#print ('eps2')
			return False

		return True
		#if 'K' stock_dict['Avg Volume'] or :

# Optionable
# Avg Volume
# EPS (ttm)
# EPS next Y
# EPS next Q
# EPS this Y
# EPS next 5Y
# EPS past 5Y
# EPS Q/Q
	def analysis_document(self, workers_num, stock_queues):
		"""
		calculating the supporting point and stress point
		"""
		while not stock_queues.empty():
			stock_name = stock_queues.get()
			if not self.analysis_statement(stock_name):
				continue

			sav_csv_path = '{}.csv'.format(os.path.join(self.stock_folder_path, stock_name))
			#data = yf.download("{}".format(stock_name[0:stock_name.find('.')]), start="1960-01-01", end="2020-12-31")
			#data.to_csv(sav_csv_path)
			df = self.crawl_price(stock_name)
			if len(df) < self.ma_days:
				continue
			self.get_supporting_point(stock_name, sav_csv_path)
			print ('worker number {}, stock_name is {}'.format(workers_num, stock_name))
			#time.sleep(1)

	@staticmethod
	def crawl_price(stock_id):
		now = int(datetime.datetime.now().timestamp())+86400
		url = "https://query1.finance.yahoo.com/v7/finance/download/" + stock_id + "?period1=0&period2=" + str(now) + "&interval=1d&events=history&crumb=hP2rOschxO0"
		response = requests.post(url)

		with open('stocks/{}.csv'.format(stock_id), 'w') as f:
			f.writelines(response.text)
		try:
			df = pd.read_csv('stocks/{}.csv'.format(stock_id), index_col='Date', parse_dates=['Date'])
		except:
			return []
		return df

class Boss(object):
	def __init__(self, stock_name_list):
		count = 0
		self.stock_queues = queues.Queue(len(stock_name_list), ctx=multiprocessing)
		for stock_name in stock_name_list:
			self.stock_queues.put(stock_name)
		self.workers = []


	def load_config(self, config_path):
		"""
		loading information from configure file
		input:
			the path of configure file
		output:
			self.stock_list: [stock name 1, stock name 2, ....]
			self.period_days: v shape, from 100 to 100*(1-self.difference_rate) in self.period_days days, and 
						100*(1-self.difference_rate) to 100*(1-self.difference_rate)*(1+self.difference_rate)
						in self.period_days days, 100*(1-self.difference_rate) is supporting_point
			self.difference_rate: ↑

		"""

		with open(config_path,'r') as config_file:
			config_lines = config_file.readlines()
			self.stock_folder_path = config_lines[0].strip()
			if not os.path.exists(self.stock_folder_path):
				os.makedirs(self.stock_folder_path)
			self.num_worker = int(config_lines[2].strip())
			self.period_days = int(config_lines[3].strip())
			self.difference_rate = float(config_lines[4].strip())
			self.roe_ttm = float(config_lines[5].strip())

	def hire_worker(self):
		"""
		using multiprocess to process .csv, we will enable self.num_worker thread to process data
		"""
		for i in range(self.num_worker):
			trader = copy.deepcopy(Trader(self.period_days, self.difference_rate, self.stock_folder_path, self.roe_ttm))
			print ('worker {}'.format(i))
			self.workers.append(trader)

	def assign_task(self):
		for i in range(self.num_worker):
			p = Process(target=self.workers[i].analysis_document, args=(i, self.stock_queues,))
			p.start()
			p.join(timeout=0.1)

			#p = Process(target=self.workers[i].analysis_document, args=(i, self.stock_queues,))
			#p.start()
			#p.join(timeout=0.1)

		print ('assign task finish!')


def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--config_path', type=str)
	return parser.parse_args()

def main():
	param = get_args()
	boss = Boss(get_stock_name_list())
	boss.load_config(param.config_path)
	boss.hire_worker()
	boss.assign_task()
	print ('completed!')

def get_stock_name_list():
	from finviz.screener import Screener

	filters = ['exch_nasd']  # Shows companies in NASDAQ which are in the S&P500
	# Get the first 50 results sorted by price ascending
	stock_list = Screener(filters=filters)

	# Export the screener results to .csv
	stock_list.to_csv()

	# Create a SQLite database
	stock_list.to_sqlite()

	stock_name_list = []
	for stock_dict in stock_list.data:
		stock_name_list.append(stock_dict['Ticker'])
	return stock_name_list

def main_temp():
	period_days = 5
	difference_rate = 0.1
	stock_folder_path = 'stocks'
	roe_ttm = 1
	t = Trader(period_days, difference_rate, stock_folder_path, roe_ttm)
	stock_name = '1215.TW'#'ACGL'
	file_path = 'stocks/{}.csv'.format(stock_name)
	#print (len(t.crawl_price(stock_name)))
	#data = yf.download("{}".format(stock_name[0:stock_name.find('.')]), start="1960-01-01", end="2019-09-13")
	#data.to_csv(file_path)
	t.get_supporting_point(stock_name, file_path)




if __name__ == '__main__':
	#main()
	main_temp()
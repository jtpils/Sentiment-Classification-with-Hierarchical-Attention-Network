from __future__ import print_function, division
import os
import torch
from utils import setup_logger
from model import HA_NET
from torch.autograd import Variable
import time
import numpy as np
from constants import *


def test(args, shared_model, dataset_path):
	start_time = time.time()
	log = setup_logger(0, 'epoch%d_test' % args.epoch, os.path.join(args.log_dir, 'epoch%d_test_log.txt' % args.epoch))
	log.info(
		'Test time ' + time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - start_time)) + ', ' + 'Start testing.')
	local_model = HA_NET(Embedding_Dim[Tag_Dict[args.tag]])
	local_model.load_state_dict(shared_model.state_dict())
	if args.gpu:
		local_model = local_model.cuda()

	dataset = np.load(dataset_path)
	targets = dataset["arr_0"]

	correct_cnt = 0
	TP = FP = TN = FN = 0

	for idx in range(targets.shape[0]):
		data = dataset["arr_%d" % (idx + 1)]
		if data.shape[0] == 0:
			continue
		data = Variable(torch.from_numpy(data))
		if args.gpu:
			data = data.cuda()
		target = int(targets[idx])
		output = local_model(data)

		if (output.data.cpu().numpy()[0] < 0.5 and target == 0) or (
				output.data.cpu().numpy()[0] >= 0.5 and target == 1):
			correct_cnt += 1

		pred = output.data.cpu().numpy()[0]

		if pred < 0.5 and target == 0:
			TN += 1
		elif pred >= 0.5 and target == 0:
			FN += 1
		elif pred < 0.5 and target == 1:
			FP += 1
		else:
			TP += 1

		if (idx + 1) % 100 == 0:
			log.info('Test time ' + time.strftime("%Hh %Mm %Ss", time.gmtime(
				time.time() - start_time)) + ', ' + 'Accuracy: %d / %d\t%0.4f' % (
			         correct_cnt, idx + 1, correct_cnt / (idx + 1)))

	Precision_pos = TP / (TP + FP) if TP + FP != 0 else 0
	Precision_neg = TN / (TN + FN) if TN + FN != 0 else 0
	Recall_pos = TP / (TP + FN) if TP + FN != 0 else 0
	Recall_neg = TN / (TN + FP) if TN + FP != 0 else 0
	F1_pos = 2 * Precision_pos * Recall_pos / (Precision_pos + Recall_pos)
	# F1_neg = 2 * Precision_neg * Recall_neg / (Precision_neg + Recall_neg)

	log.info('Precision = %0.2f%%' % (100 * Precision_pos) + '  Recall = %0.2f%%' % (100 * Recall_pos) + '  F1 = %0.2f%%' % (100 * F1_pos))
	log.info('Overall accuracy = %0.2f%%' % (100 * correct_cnt / targets.shape[0]))

	return correct_cnt / targets.shape[0]

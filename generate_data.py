# SPDX-FileCopyrightText: Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# SPDX-License-Identifier: MIT-0
# Generates Dummy Sensor data in a DynamoDB table for the blog Simplifying Patient Care with a Custom Voice Assistant using Amazon Lex V2 and PocketSphinx

from datetime import datetime
import random
import boto3
import json
import time

#Change if you named your table differently
table_name = 'PatientSensorInformation'

dynamodb = boto3.client('dynamodb')
names = ['Lawson Norman','Killian Case','Esmeralda Tate','Campbell Morales','Bridget Jefferson','Avery Knox','Adrien Blackwell','Aileen Rocha','Allison Moreno','Reyna Hendrix','Esteban Paul','Paige Pennington','Tyrone Dorsey','Rashad Henry','Alejandra Valencia','Lana Maddox','Cristopher Bradley','Gunnar Callahan','Juliette Wiggins','Eden Rasmussen','Zackery West','Jocelynn Joseph','Jorge Prince','Frankie Carney','Brodie Banks','Melina Woodward','Yazmin Wright','Dawson Carroll','Reagan Yates','Mila Nixon','Carlie Massey','Zachery Bryan','Dillon Buckley','Justice Lucas','Mallory Bauer','Vincent Duran','Cristofer Weeks','Mary Cuevas','Holly Griffith','Priscilla Sims','Jay Mosley','Zariah Moses','Brennan Clayton','Korbin Harper','Tori Lane','Cale Rubio','Dominique Ramirez','Sonny Page','Avery Thomas','Jazlynn Flynn','Valerie Yates','Sydnee Bautista','Alan Orr','Serena Cervantes','Emely Murray','Porter Quinn','Pierre Taylor','Sienna Rowe','Kasey Luna','Reid Mosley','Abby Mcconnell','Jeffery Larson','Kasey Cardenas','Tripp Perez','Julia Dickerson','Killian Roman','Moriah Gentry','Stephen Rojas','Desmond Dudley','Skylar Mccann','Azaria Craig','Janae Church','Arabella Delgado','Keely Bishop','Ryland Shepherd','Emily Duncan','Camron Morton','Amelia Horn','Paige Schneider','Jamie Palmer','Cierra Huynh','Isai Baker','Kenny Lara','Violet Sampson','Greta David','Adriana Holland','Nancy Rowland','Lauren Martinez','Fabian Chandler','Brady Molina','Raphael Doyle','Isabella Caldwell','Joyce Carter','Jaidyn Lloyd','Sean Adkins','Victoria Edwards','Bailey Hayden','Aileen Rasmussen','Kamari Steele','Sara Church']
sensor_types = ['blood pressure', 'blood glucose', 'heart rate', 'respiratory rate', 'body temperature']

def main():
	print("Generating Patient Sensor Data now...")
	print("Press CTRL-C to stop generating data")
	while 1:
		date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
		count = 0
		for name in names:
			blood_pressure = generate_blood_pressure()
			glucose = str(float(random.randrange(8000,20000))/100)
			heart_rate = str(random.randrange(40, 200))
			respiratory_rate = str(random.randrange(1, 40))
			body_temp = str(float(random.randrange(9650, 10300))/100)
			data = {
				'blood_pressure': blood_pressure,
				'blood_glucose': glucose,
				'heart_rate': heart_rate,
				'respiratory_rate': respiratory_rate,
				'body_temperature': body_temp
			}
			data = json.dumps(data)

			response = dynamodb.put_item(
				TableName = table_name,
				Item={
					'PATIENT_ID': {'S': str(count)},
					'TIMESTAMP': {'S': date},
					'NAME': {'S': names[count]},
					'DATA': {'S': data}
				}
			)
			count+=1
			time.sleep(0.5)

def generate_blood_pressure():
	systolic = random.randrange(100, 200)
	diastolic = random.randrange(systolic-60, systolic, 1)
	blood_pressure = str(systolic) + "/" + str(diastolic)
	return blood_pressure

if __name__ == "__main__":
	main()
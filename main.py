import os
import osu_irc
import sqlite3
from flask import Flask, render_template, request
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime
from threading import Thread
from markupsafe import escape

load_dotenv()

class ChatListener(osu_irc.Client):
	# Database instructions
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.db_connection = sqlite3.connect('logs.db')
		self.createTable()

	def createTable(self):
		cursor = self.db_connection.cursor()
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS log (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_name TEXT,
				room_name TEXT,
				content TEXT,
				timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
			)
		''')
		self.db_connection.commit()
		
	def insertLog(self, data):
		cursor = self.db_connection.cursor()
		cursor.execute('''
			INSERT INTO log (user_name, room_name, content)
			VALUES (?, ?, ?)
		''', (escape(data["user_name"]), escape(data["room_name"]), escape(data["content"])))
		self.db_connection.commit()

		logger.debug(data["content"])

	# IRC instructions
	async def onReady(self):
		await self.joinChannel("#osu")
		
		logger.info("Authenticated to IRC server. Awaiting messages.")
	
	async def onMessage(self, message):
		if message.is_private:
			return "Private message, skipping."

		if message.is_action:
			return "Action, skipping."

		self.insertLog({
			"user_name": message.user_name,
			"room_name": message.room_name,
			"content": message.content,
		})	

# Web server instructions
app = Flask(__name__)

@app.route('/')
def webserverIndex():
	return render_template('index.html')

@app.route('/search')
def webserverSearch():
	query = escape(request.args.get('query', ''))
	page = request.args.get('page', 1, type=int)
	
	connection = sqlite3.connect('logs.db')
	cursor = connection.cursor()
	
	limit = 25
	offset = (page - 1) * limit

	# Count total results
	cursor.execute('''
		SELECT COUNT(*) FROM log
		WHERE content LIKE ? OR user_name = ?
	''', ('%' + query + '%', query))
	total_results = cursor.fetchone()[0]
	total_pages = (total_results + limit - 1) // limit

	cursor.execute('''
		SELECT * FROM log
		WHERE content LIKE ? OR user_name = ?
		ORDER BY timestamp DESC
		LIMIT ? OFFSET ?
	''', ('%' + query + '%', query, limit, offset))

	results = cursor.fetchall()
	connection.close()
	
	return render_template('search.html',
		search_query=query,
		search_results=results,
		page=page,
		total_pages=total_pages,
		total_results=total_results
	)

def startFlask():
	app.run(host='0.0.0.0', port=5000)

def main():
	# https://osu.ppy.sh/home/account/edit#legacy-api
	listener = ChatListener(
		token = os.getenv('LEGACY_API_IRC_SERVER_PASSWORD'),
		nickname = os.getenv('LEGACY_API_IRC_SERVER_USERNAME') 
	)
	
	flask_thread = Thread(target=startFlask)
	flask_thread.start()

	listener.run()

if __name__ == "__main__":
	main()

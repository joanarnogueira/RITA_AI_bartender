import os
import openai
from flask import Flask, redirect, render_template, request, url_for, session
import sqlite3
import datetime
from datetime import timedelta
import pandas as pd
currentDateTime = datetime.datetime.now()

app = Flask(__name__)

secret_file = open('credentials.txt')
key = secret_file.readline()
secret_file.close()

openai.api_key = key

con = sqlite3.connect('rita_bartender.db', check_same_thread=False)
c = con.cursor()

@app.route("/", methods=("GET", "POST"))
def main():
    if request.method == 'GET':
        return render_template('main.html')
    else:
        global name
        name = request.form['name']
        age = request.form['age']
        global email
        email = request.form['email']
        email_exist = c.execute("SELECT EXISTS(SELECT 1 FROM user WHERE email=(?))", (email,)).fetchone()
        if email_exist == (0,):
            c.execute("""INSERT INTO user(name, age, email) 
               VALUES (?,?,?)""",(name,age,email))
            con.commit()
            print("Record successfully added")
    
        return render_template('main2.html', name=name)

@app.route("/login", methods=("GET", "POST"))
def login():
    return render_template('login.html')

@app.route("/profile", methods=("GET", "POST"))
def profile():
    if request.method == 'GET':
        global user_id
        global cocktails_info
        user_id = c.execute("SELECT user_id FROM user WHERE email=(?)", (email,)).fetchone()
        cocktails_info = pd.read_sql_query(f"SELECT cocktail_name, cocktail_recipe_gen, time_stamp FROM cocktails WHERE user_id ={user_id[0]} ORDER BY time_stamp DESC", con = con)
        ingredients_info = pd.read_sql_query(f"SELECT ingredient_name, cocktail_recipe_gen, time_stamp FROM ingredients WHERE user_id ={user_id[0]} ORDER BY time_stamp DESC", con = con)
        ingredients_info.rename(columns={'ingredient_name':'Ingredient Searched', 'cocktail_recipe_gen':'RITA Recipe', 'time_stamp': 'Searched On'}, inplace=True)
        cocktails_info.rename(columns={'cocktail_name':'Cocktail Searched', 'cocktail_recipe_gen':'RITA Recipe', 'time_stamp': 'Searched On'}, inplace=True)
        con.commit()

        return render_template('profile.html', tables =[cocktails_info.to_html(classes='data', index=False), ingredients_info.to_html(classes='data', index=False)], titles= [' '], name=name)
        #column_names_cocktails=cocktails_info.columns.values, row_data_cocktails=list(cocktails_info.values.tolist()), zip=zip )
        #,titles= [' ', 'From Cocktail', 'From Ingredient'],
@app.route("/ingredient", methods=("GET", "POST"))
# first function to get cocktail from ingredient input 

def cocktail_from_ingredient():

    if request.method == "POST":
        ingredient = request.form["ingredient"]
        app.logger.info(ingredient)
        response1 = openai.Completion.create(
            model="text-davinci-002",
            prompt= generate_cocktail(ingredient),
            temperature=0.7,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
            )
        global email
        user_id = c.execute("SELECT user_id FROM user WHERE email= (?)", (email,)).fetchone()[0]
        currentDateTime = datetime.datetime.now()

        app.logger.info("Cocktail Recipe:")
        app.logger.info(response1)

        c.execute("""INSERT INTO ingredients(ingredient_name, cocktail_recipe_gen, time_stamp, user_id) 
               VALUES (?, ?, ?, ?)""", (ingredient, response1.choices[0].text, currentDateTime, user_id))
        con.commit()

        return render_template('ingredient.html', result=response1.choices[0].text, ingredient=ingredient)
    
    else:
        return render_template('ingredient.html')



#generate cocktail from ingredient(input)
def generate_cocktail(ingredient):
    return """"
    Ingredient: gin
    Recipe: Negroni- 30ml Gin, 30ml Campari, 30ml Red Vermouth
    
    Ingredient: cointreau
    Recipe: Cotton Candy Fizz- 30ml Cointreau, 30ml Lemon Juice, 10ml Grenadine, Add Sprite

    Ingredient: vodka
    Recipe: Screwdriver-50 ml Vodka, 40ml  Orange Juice

    Ingredient: champagne
    Recipe: French 75- 45ml Gin, 15ml Lemon Juice, 7.5ml Simple Syrup, Top with Champagne
    Ingredient: {}
    Recipe:""".format(ingredient.capitalize())

#second function to generate recipe from cocktail name
@app.route("/cocktail", methods=("GET", "POST"))
def recipe_from_cocktail():

    if request.method == "POST":

        cocktail = request.form["cocktail"]
        app.logger.info(cocktail)
        response2 = openai.Completion.create(
            model="text-davinci-002",
            prompt= generate_recipe(cocktail),
            temperature=0.7,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=["\n"]
            )
        
        global email
        user_id = c.execute("SELECT user_id FROM user WHERE email= (?)", (email,)).fetchone()[0]

        currentDateTime = datetime.datetime.now()

        app.logger.info("Cocktail Recipe:")
        app.logger.info(response2)
        c.execute("""INSERT INTO cocktails(cocktail_name, cocktail_recipe_gen, time_stamp, user_id) 
               VALUES (?, ?, ?, ?)""", (cocktail, response2.choices[0].text, currentDateTime, user_id))
        con.commit()        
        return render_template('cocktail.html', result2=response2.choices[0].text, cocktail=cocktail)
    else:
        return render_template('cocktail.html')

# generate cocktail recipe from cocktail name

def generate_recipe(cocktail):
    return """"
    Cocktail: long island ice tea
    Recipe: 15ml vodka, 15ml rum, 15ml gin, 15ml tequila, 15ml triple sec, 30ml sweet and sour mix, 30ml cola, 1 lemon slice

    Cocktail: pornstar martini
    Recipe: 45 ml vanilla flavored vodka, 15ml passion fruit liqueur, 30ml passion fruit puree, 15ml lime juice, 60ml sparkling wine

    Cocktail: strawberry daiquiri
    Recipe: 500g strawberries, 200g ice, 100ml rum, lime juice, sugar syrup

    Cocktail: {}
    Recipe:""".format(cocktail.capitalize())

if __name__ == '__main__':
    app.run(debug=True, port=5005)
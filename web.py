from flask import Flask, jsonify, request
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
from tinydb import TinyDB, Query
import os
import re

#PARTE2
app = Flask(__name__)
#ATIVANDO O DB
db = TinyDB('db.json')

#PARTE3
@app.route('/api/v1/filmes', methods=['GET'])
def filmes():
  #MEU CODIGO AQUI
   html_kino = urlopen("https://www.kinoplex.com.br/cinema/37").read()

   html_cinesystem = urlopen("https://www.cinesystem.com.br/cinemas/rio-anil-shopping/856").read()

   user_agent = 'Mozilla/5.0 (Linux; U; Linux 4.2; pt-BR; rv:4.2.5) Gecko/2017121101 Firefox/51.0.0'
   url = "http://www.google.com.br/search?safe=off&q=filmes"
   headers = {'User-Agent':user_agent,}

   request = Request(url, None, headers)
   response = urlopen(request)
   html_docg = response.read()

   #soup = BeautifulSoup(html_docg, "html.parser")

   kinoplex = BeautifulSoup(html_kino, "html.parser")
   cinesystem = BeautifulSoup(html_cinesystem, "html.parser")

   data = []
   ###AQUI CINESYSTEM
   for prog in cinesystem.find_all(id="programacao_cinema"):
     for dataBox in prog.find_all(class_="row"):
       nomeFilme = dataBox.find("a")
       #Nesse cinema vem a sala, se eh leg ou dub e se eh 3D
       dub_leg = dataBox.find("div", class_="col-xs-10 painel-salas-info").text.strip()
       sala = dataBox.find("h4", class_="num-sala").text.strip()
       horarios = dataBox.find("ul", class_="list-inline-item")
       data.append({   'cinema': "CINESYSTEM",
                        'filme': nomeFilme.text.strip(),
                        'poster' : "",
                        'sinopse' : "",
                        'sala': sala,
                        'dub_leg' : dub_leg,
                        'horarios': horarios.text.replace("comprar","").split()
                        })

   ### AQUI KINOPLEX
   for dataBox in kinoplex.find_all("div", class_="cinema-programacao"):
       nomeFilme = dataBox.find("a", class_="header-link")
       #Nesse cinema vem a sala, se eh leg ou dub e se eh 3D
       sala_leg_3d = dataBox.find("h6", class_=re.compile("^card-subtitle mb-2"))
       regex = "^([1-9])(LEG|DUB|)(3D|)$"
       sala_leg_3d = re.compile(regex).split(sala_leg_3d.text.strip().replace('Sala ',''))
       horarios = dataBox.find("span", class_=re.compile("^horarios-sessao"))
       data.append({   'cinema': "Kinoplex",
                       'filme': nomeFilme.text.strip(),
                       'poster' : "",
                       'sinopse' : "",
                       'sala': sala_leg_3d[1],
                       'dub_leg' : sala_leg_3d[2],
                       'horarios': horarios.text.replace("-","").split()
                       })

   db.purge()
   db.all()
   for filme in data:
       db.insert(filme)

   return jsonify({'filmes': data, 'salas':'/api/v1/salas/<filme>', 'sessoes':'/api/v1/sessoes/<horario>', 'cinema':'/api/v1/<cinema>'})

@app.route('/api/v1/salas/<filme>', methods=['GET'])
def listaSalasFilme(filme):
   Mov = Query()
   print("Aqui")
   return jsonify({'filmes': db.search(Mov.filme.search(filme.upper()))})


@app.route('/api/v1/sessoes/<horario>', methods=['GET'])
def listaSessaoHorario(horario):
   print(horario)
   Mov = Query()
   return jsonify({'filmes': db.search(Mov.horarios.any([horario]))})

@app.route('/api/v1/<cinema>', methods=['GET'])
def listaFilmesCinema(cinema):
   print(cinema.upper())
   Mov = Query()
   return jsonify({'filmes': db.search(Mov.cinema.any(cinema)),'salas': '/api/v1/'+cinema+'/sessoes/<filme>'})

@app.route('/api/v1/<cinema>/sessoes/<filme>', methods=['GET'])
def listaSalasFilmeNoCinema(cinema,filme):
   print(cinema)
   Mov = Query()
   return jsonify({'filmes': db.search( ((Mov.cinema.any(cinema)) & (Mov.filme.any(filme.upper())))  ),
                   'salas': '/api/v1/cinemas/'+filme})


#PARTE4
if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)

#!/usr/bin/env python

from lib_mv import MV, Red, network
import logging, sys, os, subprocess, json
from subprocess import call
from lxml import etree


logging.basicConfig(level=logging.DEBUG)
logger= logging.getLogger('auto-p2')


def init_log():
    # Creacion y configuracion del logger
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('auto_p2')
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    log.addHandler(ch)
    log.propagate = False

def pause():
    programPause = raw_input("Press the <ENTER> key to continue...")
    
with open('auto-p2.json', 'r') as archivo_json:
	datos_json = json.load(archivo_json)
	
numServidores = datos_json['num_serv']
if numServidores > 5 :
	print("El número de servidores debe ser menor o igual que 5, cambia el json")
	sys.exit()    

# Main
init_log()
print('CDPS - mensaje info1')
print("Creado por:")
print("Mónica Ortega, Claudia Sánchez y Javier Montesinos")
print()
def crear(numServidores):
	c1 = MV("c1")
	c1.crear_mv()
	lb = MV("lb")
	lb.crear_mv()

	for n in range(0, numServidores):
		parseo = str(n+1)
		name = "s" + parseo
		server = MV(str(name))
		server.crear_mv()
	
	LAN1 = Red('LAN1')
	LAN1.crear_red()
	LAN2 = Red('LAN2')
	LAN2.crear_red()
	call(["sudo", "ifconfig", "LAN1", "10.11.1.3/24"])
	call(["sudo", "ip", "route", "add", "10.11.0.0/16", "via", "10.11.1.1"])

	
	logger.debug("Escenario creado correctamente")
	
def arrancar(server):
	aux = server
	if aux == "todas":
		c1 = MV('c1')
		c1.arrancar_mv()
		lb = MV('lb')
		lb.arrancar_mv()

		for n in range(0, numServidores):
			parseo = str(n+1)
			name = "s" + parseo
			server = MV(str(name))
			server.arrancar_mv()
	else :
		server = MV(server)
		server.arrancar_mv()


	logger.debug("Escenario arrancado correctamente")
def parar(server) :
	aux = server
	if aux == "todas":
		c1 = MV('c1')
		c1.parar_mv()
		lb = MV('lb')
		lb.parar_mv()

		for n in range(0, numServidores):
			parseo = str(n+1)
			name = "s" + parseo
			server = MV(str(name))
			server.parar_mv()
	else :
		server = MV(server)
		server.parar_mv()

	logger.debug("Escenario detenido correctamente")


def liberar() :
	c1 = MV('c1')
	c1.liberar_mv()
	lb = MV('lb')
	lb.liberar_mv()

	for n in range(0, numServidores):	
		parseo = str(n+1)
		name = "s" + parseo
		server = MV(str(name))
		server.liberar_mv()
	
	eth0 = Red('LAN1')
	eth0.liberar_red()
	eth1 = Red('LAN2')
	eth1.liberar_red()

	logger.debug("Escenario destruido correctamente")

def watch(): 
	os.system("xterm -title monitor -e watch sudo virsh list --all & ")

def ping(server):
	os.system("ping -c 2 " + network[server][0] )	


def help():
	mensaje = """ 
	❧  Se pueden ejecutar los siguientes comandos: ☙
	➜ crear, crea escenario p2.
	➜ arrancar, para arrancar todas las MV. Añadir el nombre de una o varias MV para arrancarlas individualmente. 
	➜ parar, para parar todas las MV. Añadir el nombre de una o varias MV para pararlas individualmente. 
	➜ liberar, para escenario y borra archivos.
	➜ watch, muestra el estado de todas las MV.
	➜ dominfo, muestra información de huésped.
	➜ domstate, muestra el estado de un huésped.
	➜ cpu, muestra el gasto de las CPUs que utiliza la MV.
	➜ ping, comprueba la conectividad con las MVs desde el host.
	"""
	print(mensaje)	



#Ejecucion
argumentos = sys.argv
if len(argumentos) == 2 :
	if argumentos[1] == "crear":
		crear(numServidores)
	if argumentos[1] == "liberar":
		liberar()
	if argumentos[1] == "watch":
		watch()
	if argumentos[1] == "parar":
		parar("todas")
	if argumentos[1] == "arrancar":
		arrancar("todas")		
	if argumentos[1] == "help":
		help()
	
if len(argumentos) >= 3 :
	if argumentos[1] == "arrancar":
		for server in argumentos[2:]:
			arrancar(server)
	if argumentos[1] == "parar":
		for server in argumentos[2:]:
			parar(server)
	if argumentos[1] == "dominfo":	
		for server in argumentos[2:]:
			os.system("sudo virsh dominfo " + server)
	if argumentos[1] == "domstate":	
		for server in argumentos[2:]:
			os.system("sudo virsh domstate " + server)
	if argumentos[1] == "cpu":	
		for server in argumentos[2:]:
			os.system("sudo virsh cpu-stats " + server)		
	if argumentos[1] == "ping":
		for server in argumentos[2:]:
			ping(server)
			print()
			print("⚠️  Comprueba que la MV seleccionada y el LB estén arrancados")




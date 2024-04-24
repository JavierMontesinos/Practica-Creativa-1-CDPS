import logging, os, subprocess
from subprocess import call
from lxml import etree


log = logging.getLogger('auto_p2')

servers = ["s1", "s2", "s3", "s4" ,"s5"]
bridges = {"c1":["LAN1"],
          "lb":["LAN1"],
          "s1":["LAN2"],
          "s2":["LAN2"],
          "s3":["LAN2"],
          "s4":["LAN2"],
          "s5":["LAN2"]}
network = {
          "c1":["10.11.1.2", "10.11.1.1"],
          "s1":["10.11.2.31", "10.11.2.1"],
          "s2":["10.11.2.32", "10.11.2.1"], 
          "s3":["10.11.2.33", "10.11.2.1"],
          "s4":["10.11.2.34", "10.11.2.1"],
          "s5":["10.11.2.35", "10.11.2.1"]}




def configuraXML(sistema) :

  #Se obtiene el directorio de trabajo
  cwd = os.getcwd()  #método de OS que devuelve el Current Working Directory
  path = cwd + "/" + sistema
  #path = "/Desktop/Creativa/"
  
  #Se importa el .xml de la máquina pasada como parámetro utilizando métodos de la librería LXML
  tree = etree.parse(path + ".xml")
  
  root = tree.getroot()

  #Se define el nombre de la MV
  name = root.find("name")
  name.text = sistema

  #Se define el nombre de la imagen, cambiando la ruta del source de la imagen (disk) al qcow2 correspondiente a la maquina pasada como parametro
  sourceFile = root.find("./devices/disk/source")
  sourceFile.set("file", path + ".qcow2")

  #Se definen los bridges, modificando el XML con los bridges correspondientes a la maquina parámetro
  bridge = root.find("./devices/interface/source")
  bridge.set("bridge", bridges[sistema][0])  #se cambia el valor de la etiqueta <source bridge> por la LAN (el bridge) correspondiente a la máquina pasada como parametro
  
  fout = open(path + ".xml", "w")  #se crea fout con el método open y el modo W, que abre un archivo para sobreescribir su contenido y lo crea si no existe
  fout.write(etree.tounicode(tree, pretty_print = True))  #convierte en serie el elemento a la representación unicode de Python de su arbol XML. Pretty_print a true habilita XMLs formateados.
  fout.close()
  if sistema == "lb":
    fin = open(path + ".xml",'r')   #fin es el XML correspondiente a lb, en modo solo lectura
    fout = open("temporal.xml",'w')  #fout es un XML temporal abierto en modo escritura
    for line in fin:
      if "</interface>" in line:
        fout.write("</interface>\n <interface type='bridge'>\n <source bridge='"+"LAN2"+"'/>\n <model type='virtio'/>\n </interface>\n")
      #si el XML de lb contiene un interface (que lo va a contener, ya que previamente se le habrá añadido el bridge LAN1), se le añade al XML temporal otro bridge: LAN2
      else:
        fout.write(line)
    fin.close()
    fout.close()

    call(["cp","./temporal.xml", path + ".xml"])  #sustituimos es XML por el temporal, que es el que contiene las dos LAN
    call(["rm", "-f", "./temporal.xml"])


#Configuración del hostname y los interfaces de red de las maquinas virtuales
def configuraRed(sistema):

  cwd = os.getcwd()
  path = cwd + "/" + sistema

  #Configuración del hostname
  fout = open("hostname",'w')  
  fout.write(sistema + "\n")  
  fout.close()
  call(["sudo", "virt-copy-in", "-a", sistema + ".qcow2", "hostname", "/etc"])
  call(["rm", "-f", "hostname"])

  #Configuracion del host, que asigna nombres de host a direcciones IP
  #Asigna la direccion IP local a la maquina pasada como parametro
  call("sudo virt-edit -a " + sistema + ".qcow2 /etc/hosts -e 's/127.0.1.1.*/127.0.1.1 " + sistema + "/'", shell=True)

  #Configuracion de los interfaces de red de las maquinas virtuales
  fout = open("interfaces",'w')
  if sistema == "lb":   #si la maquina es el balanceador lb, añade a interfaces sus dos interfaces correspondientes a LAN1 y LAN2
    fout.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet static\n  address 10.11.1.1\n netmask 255.255.255.0\n gateway 10.11.1.1\nauto eth1\niface eth1 inet static\n  address 10.11.2.1\n netmask 255.255.255.0\n gateway 10.11.2.1")
  else:  #si no, añade la direccion IP correspondiente a la maquina, y la direccion del LB en gateway
    fout.write("auto lo \niface lo inet loopback\n auto eth0\n iface eth0 inet static\n address " + network[sistema][0] +"\nnetmask 255.255.255.0 \n gateway " + network[sistema][1] + "\n")
  fout.close()
  call(["sudo", "virt-copy-in", "-a", sistema + ".qcow2", "interfaces", "/etc/network"])
  call(["rm", "-f", "interfaces"])

  #Se habilita forwarding IPv4 para que lb funcione como router al arrancar
  if sistema == "lb":
    call("sudo virt-edit -a lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'", shell=True)
        

    
class MV:
  def __init__(self, nombre):
    self.nombre = nombre
    log.debug('init MV ' + self.nombre)
    
  def crear_mv (self, imagen = None, interfaces_red = None, router = None):
    log.debug("crear_mv " + self.nombre)
    #Se crean las MVs y las redes que forman el escenario a partir de la imagen base
    call(["qemu-img","create", "-f", "qcow2", "-b", "./cdps-vm-base-pc1.qcow2",  self.nombre + ".qcow2"])
    #Se modifican los ficheros XML de todas las máquinas del escenario
    call(["cp", "plantilla-vm-pc1.xml", self.nombre + ".xml"])
    sistema = self.nombre
    configuraXML(sistema)
    call(["sudo", "virsh", "define", self.nombre + ".xml"])
    sistema = self.nombre
    configuraRed(sistema)
  
          
  def arrancar_mv (self):
    log.debug("arrancar_mv " + self.nombre)
    call(["sudo", "virsh", "start", self.nombre])
    os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title '" + self.nombre + "' -e 'sudo virsh console "+ self.nombre + "' &")

  def mostrar_consola_mv (self):
    log.debug("mostrar_mv " + self.nombre)

  def parar_mv (self):
    log.debug("parar_mv " + self.nombre)
    call(["sudo", "virsh", "shutdown", self.nombre])

  def liberar_mv (self):
    log.debug("liberar_mv " + self.nombre)
    call(["sudo", "virsh", "destroy", self.nombre])
    call(["sudo", "virsh", "undefine", self.nombre])
    call(["rm", "-f",  self.nombre + ".qcow2"])
    call(["rm", "-f",  self.nombre + ".xml"])
    

class Red:
  def __init__(self, nombre):
    self.nombre = nombre
    log.debug('init Red ' + self.nombre)

  def crear_red(self):
      log.debug('crear_red ' + self.nombre)
      call(["sudo", "brctl", "addbr", self.nombre])
      call(["sudo", "ifconfig", self.nombre, "up"])   

  def liberar_red(self):
      log.debug('liberar_red ' + self.nombre)
      call(["sudo", "ifconfig", self.nombre, "down"])
      call(["sudo", "brctl", "delbr", self.nombre])
      

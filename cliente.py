from flask import Flask, request, render_template
import socket

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # Asegúrate de tener un archivo index.html

@app.route('/transaccion', methods=['POST'])
def transaccion():
    cedula = request.form['cedula']
    monto = request.form['monto']
    tipo = request.form['tipo']
    cedula_destino = request.form.get('cedula_destino')

    if tipo == "TRANSFERIR":
        # Enviar datos al servidor
        enviar_datos(f"TRANSFERIR,{cedula},{monto},{cedula_destino}")
    elif tipo == "DEPOSITAR":
        enviar_datos(f"DEPOSITAR,{cedula},{monto}")
    elif tipo == "RETIRAR":
        enviar_datos(f"RETIRAR,{cedula},{monto}")

    return "Transacción realizada"

@app.route('/consulta', methods=['POST'])
def consulta():
    cedula_consulta = request.form['cedula_consulta']
    respuesta = enviar_datos(f"CONSULTAR,{cedula_consulta}")
    return respuesta  # Deberías mostrar esta respuesta en algún lugar

def enviar_datos(mensaje):
    try:
        cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente_socket.connect(("localhost", 9999))
        cliente_socket.send(mensaje.encode('utf-8'))
        respuesta = cliente_socket.recv(4096).decode('utf-8')
        cliente_socket.close()
        return respuesta
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)

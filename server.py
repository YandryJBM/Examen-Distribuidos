import socket
import threading
import psycopg2
from decimal import Decimal  # Importar Decimal para manejar montos correctamente

# Configurar conexión con la base de datos
def conectar_db():
    return psycopg2.connect(
        dbname="cliente_db",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )

def transferir_dinero(cedula_origen, cedula_destino, monto):
    try:
        # Crear conexión y cursor
        conexion = conectar_db()
        cursor = conexion.cursor()

        # Verificar si ambos clientes existen y obtener el saldo
        cursor.execute("SELECT saldo FROM clientes WHERE cedula = %s", (cedula_origen,))
        saldo_origen = cursor.fetchone()

        cursor.execute("SELECT saldo FROM clientes WHERE cedula = %s", (cedula_destino,))
        saldo_destino = cursor.fetchone()

        if saldo_origen and saldo_destino:
            # Convertir el monto a Decimal
            monto_decimal = Decimal(monto)

            if saldo_origen[0] >= monto_decimal:
                # Restar el monto al cliente de origen
                nuevo_saldo_origen = saldo_origen[0] - monto_decimal
                cursor.execute("UPDATE clientes SET saldo = %s WHERE cedula = %s", (nuevo_saldo_origen, cedula_origen))

                # Sumar el monto al cliente de destino
                nuevo_saldo_destino = saldo_destino[0] + monto_decimal
                cursor.execute("UPDATE clientes SET saldo = %s WHERE cedula = %s", (nuevo_saldo_destino, cedula_destino))
                
                # Confirmar cambios en la base de datos
                conexion.commit()
                return "Transferencia exitosa"
            else:
                return "Saldo insuficiente para la transferencia"
        else:
            return "Uno de los clientes no existe"

    except Exception as e:
        return f"Error en la transferencia: {str(e)}"

    finally:
        # Cerrar cursor y conexión
        cursor.close()
        conexion.close()

def depositar_dinero(cedula, monto):
    try:
        # Verificar si el monto es positivo
        if monto <= 0:
            return "El monto a depositar debe ser mayor a 0"

        conexion = conectar_db()
        cursor = conexion.cursor()

        # Verificar si el cliente existe y actualizar el saldo
        cursor.execute("SELECT saldo FROM clientes WHERE cedula = %s", (cedula,))
        saldo_actual = cursor.fetchone()

        if saldo_actual:
            monto_decimal = Decimal(monto)
            nuevo_saldo = saldo_actual[0] + monto_decimal
            cursor.execute("UPDATE clientes SET saldo = %s WHERE cedula = %s", (nuevo_saldo, cedula))
            conexion.commit()
            return "Depósito exitoso"
        else:
            return "El cliente no existe"

    except Exception as e:
        return "Error en el depósito: Cantidad Incorrecta"

    finally:
        cursor.close()
        conexion.close()

def retirar_dinero(cedula, monto):
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        # Verificar si el cliente existe y tiene saldo suficiente
        cursor.execute("SELECT saldo FROM clientes WHERE cedula = %s", (cedula,))
        saldo_actual = cursor.fetchone()

        if saldo_actual:
            monto_decimal = Decimal(monto)
            if saldo_actual[0] >= monto_decimal:
                nuevo_saldo = saldo_actual[0] - monto_decimal
                cursor.execute("UPDATE clientes SET saldo = %s WHERE cedula = %s", (nuevo_saldo, cedula))
                conexion.commit()
                return "Retiro exitoso"
            else:
                return "Saldo insuficiente para el retiro"
        else:
            return "El cliente no existe"

    except Exception as e:
        return f"Error en el retiro: {str(e)}"

    finally:
        cursor.close()
        conexion.close()

def consultar_cliente(cedula):
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()

        # Verificar si el cliente existe
        cursor.execute("SELECT nombre, apellido, saldo FROM clientes WHERE cedula = %s", (cedula,))
        cliente = cursor.fetchone()

        if cliente:
            nombre, apellido, saldo = cliente
            return f"Nombre y Apellido: {nombre} {apellido}, Saldo: {saldo}"
        else:
            return "El cliente no existe"

    except Exception as e:
        return f"Error en la consulta: {str(e)}"

    finally:
        cursor.close()
        conexion.close()

def manejar_cliente(cliente_socket):
    try:
        solicitud = cliente_socket.recv(4096).decode('utf-8')  # Recibir solicitud del cliente
        print(f"Solicitud recibida: {solicitud}")
        
        # Separar los datos recibidos
        datos = solicitud.split(",")
        
        # Procesar según la acción recibida
        if datos[0] == "TRANSFERIR":
            accion, cedula, monto, cedula_destino = datos  # acción, cédula, monto, cédula del destinatario
            monto = float(monto)
            respuesta = transferir_dinero(cedula, cedula_destino, monto)
        elif datos[0] == "CONSULTAR":
            cedula = datos[1]
            respuesta = consultar_cliente(cedula)
        else:
            accion, cedula, monto = datos  # acción, cédula, monto
            monto = float(monto)
            
            if accion == "DEPOSITAR":
                respuesta = depositar_dinero(cedula, monto)
            elif accion == "RETIRAR":
                respuesta = retirar_dinero(cedula, monto)
        
        # Enviar respuesta al cliente
        cliente_socket.send(respuesta.encode('utf-8'))
    except Exception as e:
        print(f"Error al manejar la solicitud: {str(e)}")
    finally:
        cliente_socket.close()

def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", 9999))
    servidor.listen(5)
    print("Servidor escuchando...")

    while True:
        cliente_socket, addr = servidor.accept()
        print(f"Conexión aceptada de {addr}")
        manejador_cliente = threading.Thread(target=manejar_cliente, args=(cliente_socket,))
        manejador_cliente.start()

if __name__ == "__main__":
    main()

import os
from PIL import Image

# Delimitador único para marcar el final del mensaje
DELIMITADOR = "###FIN###"

def texto_a_bits(texto):
    """Convierte texto a una cadena de bits (8 bits por carácter)."""
    return ''.join(format(ord(c), '08b') for c in texto)

def bits_a_texto(cadena_bits):
    """Convierte una cadena de bits (múltiplo de 8) de vuelta a texto."""
    texto = ""
    for i in range(0, len(cadena_bits), 8):
        byte = cadena_bits[i:i+8]
        if len(byte) < 8:
            break
        texto += chr(int(byte, 2))
    return texto

def codificar_exagerado(ruta_entrada, mensaje, ruta_salida):
    """Oculta un mensaje alterando drásticamente los bits más significativos."""
    try:
        img = Image.open(ruta_entrada).convert("RGB")
    except FileNotFoundError:
        print(f"Error: No se encontró la imagen '{ruta_entrada}'")
        return

    pixels = img.load()
    width, height = img.size

    # Preparar datos: mensaje + delimitador
    datos_ocultos = mensaje + DELIMITADOR
    bits = texto_a_bits(datos_ocultos)
    
    # Cada píxel (RGB) puede guardar 3 bits (uno por canal).
    # Necesitamos 1 píxel por cada 3 bits del mensaje.
    pizeles_necesarios = (len(bits) + 2) // 3
    
    if pizeles_necesarios > (width * height):
        print(f"Error: El mensaje es demasiado largo para esta imagen ({width}x{height}).")
        print(f"Se necesitan {pizeles_necesarios} píxeles, la imagen tiene {width*height}.")
        return

    bit_idx = 0
    modificados = 0
    
    # Recorrer la imagen píxel por píxel
    for y in range(height):
        for x in range(width):
            if bit_idx >= len(bits):
                break # Mensaje completado
            
            r, g, b = pixels[x, y]
            canales = [r, g, b]
            
            # Modificar canales RGB secuencialmente
            for i in range(3):
                if bit_idx < len(bits):
                    bit_a_insertar = int(bits[bit_idx])
                    
                    # --- CAMBIO EXAGERADO ---
                    # En lugar de modificar el bit 0 (LSB), modificamos los 4 bits altos.
                    # 'canales[i] & 0x0F' mantiene los 4 bits bajos originales.
                    # '(bit_a_insertar << 7)' o '<< 4' pone el bit del mensaje en una posición alta.
                    # Usamos '<< 7' (el bit más significativo) para el cambio máximo posible.
                    
                    if bit_a_insertar == 1:
                        # Si es 1, forzamos el bit más significativo a 1 (valor alto)
                        canales[i] = (canales[i] & 0x7F) | 0x80
                    else:
                        # Si es 0, forzamos el bit más significativo a 0 (valor bajo)
                        canales[i] = (canales[i] & 0x7F) | 0x00
                    
                    bit_idx += 1
            
            # Actualizar el píxel en la imagen
            pixels[x, y] = tuple(canales)
            modificados += 1

        if bit_idx >= len(bits):
            break

    # Guardar en PNG para no perder datos por compresión
    img.save(ruta_salida, format="PNG")
    print(f"\n[+] Éxito. Mensaje ocultado en '{ruta_salida}'")
    print(f"[+] Se modificaron {modificados} píxeles de forma visible.")
    print(f"[+] La zona modificada comienza en la esquina superior izquierda (0,0).")


def decodificar_exagerado(ruta_imagen):
    """Extrae el mensaje analizando los bits más significativos."""
    try:
        img = Image.open(ruta_imagen).convert("RGB")
    except FileNotFoundError:
        print(f"Error: No se encontró la imagen '{ruta_imagen}'")
        return None

    pixels = img.load()
    width, height = img.size
    
    bits_extraidos = ""
    mensaje_acumulado = ""

    # Recorrer píxeles para extraer bits
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            canales = [r, g, b]
            
            for valor_canal in canales:
                # --- EXTRACCIÓN DEL CAMBIO EXAGERADO ---
                # Extraemos el bit más significativo (bit 7)
                # '(valor_canal >> 7)' mueve el bit 7 a la posición 0.
                # '& 1' se asegura de aislarlo.
                bit = (valor_canal >> 7) & 1
                bits_extraidos += str(bit)
                
                # Comprobar cada 8 bits si hemos encontrado el delimitador
                if len(bits_extraidos) == 8:
                    caracter = bits_a_texto(bits_extraidos)
                    mensaje_acumulado += caracter
                    bits_extraidos = "" # Reiniciar buffer de bits
                    
                    if mensaje_acumulado.endswith(DELIMITADOR):
                        # Retornar el mensaje sin el delimitador
                        return mensaje_acumulado[:-len(DELIMITADOR)]
                        
    return None # No se encontró delimitador

# --- Menú Interactivo ---
def menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear') # Limpiar pantalla
        print("========================================")
        print("  ESTEGANOGRAFÍA VISIBLE (Ejemplo LSB Exagerado)")
        print("========================================")
        print("1. Codificar (Ocultar mensaje VISIBLEMENTE)")
        print("2. Decodificar (Leer mensaje manualmente)")
        print("3. Salir")
        print("----------------------------------------")
        
        opcion = input("Seleccione una opción (1-3): ")
        
        if opcion == '1':
            print("\n--- CODIFICAR MENSAGE ---")
            img_original = input("Introduce la ruta de la imagen original (ej: imagen.png): ")
            if not os.path.exists(img_original):
                print("Error: El archivo no existe.")
                input("\nPresiona Enter para continuar...")
                continue
                
            mensaje = input("Introduce el mensaje secreto a ocultar: ")
            img_salida = input("Introduce el nombre de la imagen de salida (ej: secreta.png): ")
            
            if not img_salida.lower().endswith('.png'):
                img_salida += ".png"
                print(f"(Se ha añadido la extensión .png automáticamente: {img_salida})")

            codificar_exagerado(img_original, mensaje, img_salida)
            input("\nPresiona Enter para continuar...")
            
        elif opcion == '2':
            print("\n--- DECODIFICAR MENSAGE (Manual) ---")
            img_secreta = input("Introduce la ruta de la imagen con el mensaje (ej: secreta.png): ")
            if not os.path.exists(img_secreta):
                print("Error: El archivo no existe.")
                input("\nPresiona Enter para continuar...")
                continue
            
            print("Decodificando la imagen...")
            mensaje_recuperado = decodificar_exagerado(img_secreta)
            
            if mensaje_recuperado:
                print("\n========================================")
                print("       MENSAJE SECRETO ENCONTRADO")
                print("========================================")
                print(mensaje_recuperado)
                print("========================================")
            else:
                print("\n[-] No se pudo encontrar un mensaje válido en esta imagen.")
                print("    (O la imagen no tiene mensaje, o usa un método/delimitador diferente).")
            
            input("\nPresiona Enter para continuar...")
            
        elif opcion == '3':
            print("\nSaliendo del programa. ¡Adiós!")
            break
        else:
            print("\nOpción no válida. Intente de nuevo.")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    # Asegurarse de que Pillow está instalado
    try:
        from PIL import Image
    except ImportError:
        print("Error: La librería 'Pillow' no está instalada.")
        print("Instálala ejecutando: pip install pillow")
        exit()
        
    menu()

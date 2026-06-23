import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_login_test():
    # =========================================================================
    # PASO 1: Configurar las opciones y arrancar el navegador Chrome
    # =========================================================================
    # Se inicializan las opciones del controlador de Chrome.
    # '--start-maximized' le indica a Chrome que inicie con la ventana maximizada.
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    
    print("[1/8] Inicializando el navegador Chrome a través de Selenium...")
    # Creamos la instancia del WebDriver. A partir de Selenium 4, Selenium Manager
    # se encarga de descargar y configurar automáticamente el ChromeDriver compatible.
    driver = webdriver.Chrome(options=options)
    
    try:
        # =========================================================================
        # PASO 2: Navegar a la página principal de producción de la tienda
        # =========================================================================
        url_tienda = "https://damabella-web.onrender.com/"
        print(f"[2/8] Navegando a la URL del sitio web: {url_tienda}")
        driver.get(url_tienda)
        
        # Damos una breve espera de 2 segundos para asegurar que los scripts iniciales carguen.
        time.sleep(2)
        
        # =========================================================================
        # PASO 3: Acceder directamente a la página de login real
        # =========================================================================
        print("[3/8] Navegando directamente a la ruta pública de inicio de sesión...")
        driver.get("https://damabella-web.onrender.com/login")
        
        # =========================================================================
        # PASO 4: Esperar la inyección de los inputs nativos en el DOM
        # =========================================================================
        print("[4/8] Esperando presencia de los campos nativos del formulario...")
        
        email_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='email'] | //input[@type='email']"))
        )
        
        password_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='password'] | //input[@type='password']"))
        )
        
        assert email_input is not None, "Error: No se pudo localizar el campo de correo electrónico."
        assert password_input is not None, "Error: No se pudo localizar el campo de contraseña."
        
        # =========================================================================
        # PASO 5: Rellenar el formulario con datos de prueba
        # =========================================================================
        # IMPORTANTE: Reemplace 'tu_email@correo.com' y 'tu_contraseña' con credenciales
        # válidas registradas en el sistema para que la prueba de login sea exitosa.
        correo_prueba = "pabonjuanjose6@gmail.com" 
        clave_prueba = "Admin1234"  # <-- REEMPLAZAR CON CONTRASEÑA REAL
        
        print(f"[5/8] Escribiendo el correo de prueba: {correo_prueba}")
        email_input.clear()
        email_input.send_keys(correo_prueba)
        
        print("[5/8] Escribiendo la contraseña de prueba...")
        password_input.clear()
        password_input.send_keys(clave_prueba)
        
        # =========================================================================
        # PASO 6: Localizar el botón de continuar/ingresar y hacer clic
        # =========================================================================
        # Buscamos el botón 'Continuar' que envía el formulario.
        print("[6/8] Localizando el botón de ingresar ('Continuar') y enviando formulario...")
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continuar')]"))
        )
        submit_button.click()
        
        # =========================================================================
        # PASO 7: Verificar con un assert que entramos correctamente al Dashboard
        # =========================================================================
        # Esperamos que el sistema valide y nos redirija a la página del panel administrativo.
        print("[7/8] Esperando redirección al Dashboard de Damabella...")
        WebDriverWait(driver, 15).until(
            EC.url_contains("/dashboard")
        )
        
        # Obtenemos la URL actual después del login.
        url_actual = driver.current_url
        print(f" -> URL actual de la página: {url_actual}")
        
        # Realizamos el assert para comprobar que la ruta contiene '/dashboard'.
        # Si la condición no se cumple, se lanzará una excepción AssertionError con el mensaje.
        assert "/dashboard" in url_actual, f"Fallo en prueba de login. URL actual inesperada: {url_actual}"
        print(" -> ASSERT CORRECTO: Login exitoso. Hemos ingresado al panel de control (Dashboard).")
        
    except Exception as error:
        print(f" -> ERROR: Ocurrió una falla durante la prueba automatizada: {error}")
        raise error
        
    finally:
        # =========================================================================
        # PASO 8: Cerrar el navegador y limpiar el proceso
        # =========================================================================
        # Este bloque 'finally' se ejecuta siempre, garantizando que el navegador
        # se cierre y libere los recursos del sistema aun si la prueba falla.
        print("[8/8] Finalizando prueba. Cerrando el navegador Chrome...")
        time.sleep(3)  # Pausa de 3 segundos para que el usuario visualice el resultado
        driver.quit()

if __name__ == "__main__":
    run_login_test()

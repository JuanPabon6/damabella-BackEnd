from rest_framework.exceptions import APIException

#objecdoesnotexists
class ObjectNotExists(APIException):
    status_code = 404
    default_detail = "Este objeto no existe"
    default_code = "No encontrado"

#integrityerror
class IntegrityException(APIException):
    status_code = 409
    default_detail = "Error de integridad"
    default_code = "Conflicto de llaves"

#multipleobjectsreturned
class MultiResults(APIException):
    status_code = 400
    default_detail = "Multiples resultados"
    default_code = "Multiples objetos"

#valueerror
class InvalidData(APIException):
    status_code = 400
    default_detail = "Datos invalidos enviados"
    default_code = "Datos invalidos"


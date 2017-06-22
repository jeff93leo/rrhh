from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta
import datetime
from dateutil import relativedelta
from dateutil import parser
import logging

class hr_employee(osv.osv):
    _inherit = "hr.employee"

    def _promedio_salario(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for employee in self.browse(cr, uid, ids, context=context):
            contrato_ids = self.pool.get('hr.contract').search(cr, uid, [('employee_id', '=', employee.id)],offset=0,limit=1,order='date_start desc')
            if len(contrato_ids) > 0:
                contrato = self.pool.get('hr.contract').browse(cr, uid, contrato_ids)[0]

                #Calculo la fecha de seis meses atras, para obtener las nominas de seis meses atras a la fecha de hoy.
                #Si la fecha de finalizacion del contrato esta vacia, utilizo la fecha de hoy como rango superior.
                if contrato.date_end:
                    fecha_seis_meses = parser.parse(contrato.date_end) - relativedelta.relativedelta(months=6)
                else:
                    fecha_seis_meses = datetime.date.today() - relativedelta.relativedelta(months=6)

                nomina_ids = self.pool.get('hr.payslip').search(cr, uid, [('employee_id', '=', employee.id), ('contract_id', '=', contrato.id), ('date_from', '>=', fecha_seis_meses)],order='date_from asc')

                salario_total = 0
                x = 0
                #Calculo el salario total, sumando cada linea de la nomina.
                #fecha_inicio sera el date_from de la primera nomina. fecha_fin sera el date_from de la ultima nomina.
                #Estas fechas sirven para calcular los meses transcurridos entre la primera nomina y la ultima, para hacer el promedio.
                for nomina in self.pool.get('hr.payslip').browse(cr, uid, nomina_ids):
                    if x == 0:
                        fecha_inicio = nomina.date_from
                    fecha_fin = nomina.date_from
                    x += 1
                    for nomina_line in nomina.line_ids:
                        salario_total += nomina_line.total

                #Si no hay nominas, regresa el promedio en 0, de lo contrario lo calcula.
                if x > 0:
                    r = relativedelta.relativedelta(parser.parse(fecha_fin), parser.parse(fecha_inicio))
                    res[employee.id] = salario_total / (r.months + 1)
                else:
                    res[employee.id] = 0
        return res

    _columns = {
        'promedio_salario': fields.function(_promedio_salario, string='Promedio Salario', digits_compute=dp.get_precision('Account')),
    }

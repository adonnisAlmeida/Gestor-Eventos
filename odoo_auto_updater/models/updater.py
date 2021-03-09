# -*- coding: utf-8 -*-
import odoo
from odoo import fields, models, api, exceptions
import logging
import base64
from io import BytesIO
import zipfile
import os
import shutil
from os.path import join as opj
from odoo.tools.osutil import tempdir
from odoo.tools import convert_file, exception_to_unicode
from odoo.http import request
import werkzeug.utils


_logger = logging.getLogger(__name__)
MAX_FILE_SIZE = 100 * 1024 * 1024  # in megabytes


class Updater(models.TransientModel):
    _name = 'res.updater'

    update_file = fields.Binary("Update File")
    state = fields.Selection([('upload', 'Upload'), ('done', 'Done'), ('restart', 'Restart')], string="State", default='upload')
        
    def rrmdir(self, dirname):
        # borrar archivos de manera recursiva
        d = os.listdir(dirname)
        for f in d:
            if os.path.isdir(dirname + '/' +f):
                self.rrmdir(dirname +'/' + f)
            else:
                os.unlink(dirname + '/' + f)
        os.rmdir(dirname)

    def import_file(self, update_file):
        if not update_file:
            raise Exception("You must upload a file.")
        if not zipfile.is_zipfile(update_file):
            raise exceptions.UserError('File is corrupted')

        update_modules = []
        install_modules = []
        with zipfile.ZipFile(update_file, "r") as z:
            for zf in z.filelist:
                if zf.file_size > MAX_FILE_SIZE:
                    raise exceptions.UserError("File '%s' exceed maximum allowed file size" % zf.filename)

            with tempdir() as temp_dir:
                try:
                    z.extractall(temp_dir)
                    if not os.path.exists(temp_dir +'/odoo_update/manifest.ini'):
                        raise exceptions.Warning("Update package does not contains a manifest.")
                    if not os.path.exists(temp_dir + '/odoo_update/files'):
                        raise exceptions.Warning("Update package does not contains files")
                    
                    # verificar la version de la actualizacion
                    update_version = '0.0.0'
                    update_minimal_version = '0.0.0'
                    restart_server = False
                    rescan_modules = False
                    try:
                        manifest = open(temp_dir + '/odoo_update/manifest.ini', 'r')
                        for line in manifest:
                            if line[:8] == "version=":
                                update_version = line[8:-1]
                            if line[:16] == "minimal_version=":
                                update_minimal_version = line[16:-1]
                            if line[:16] == "restart_server=1":
                                restart_server = True
                            if line[:16] == "rescan_modules=1":
                                rescan_modules = True
                            if line[:15] == "update_modules=":
                                mods = line[15:-1]
                                update_modules = mods.split(',')
                            if line[:16] == "install_modules=":
                                mods = line[16:-1]
                                install_modules = mods.split(',')
                        manifest.close()
                    except:
                        raise exceptions.Warning("Can not determine version of the update package")
                    
                    # verificar la version del sistema
                    installed_version = '0.0.0'
                    try:
                        module = self.env['ir.module.module'].search([('name', '=', 'odoo_auto_updater')])
                        installed_version = module[0].installed_version
                    except:
                        raise exceptions.Warning("Can not determine installed version")
                                        
                    if installed_version >= update_version:
                        raise exceptions.Warning("This update package is not necesary")
                    
                    # verificar la version minima del sistema
                    if installed_version < update_minimal_version:
                        raise exceptions.Warning("This update package requires installed version is "+ update_minimal_version +" and the actual version is " + str(installed_version))

                    files_directory = temp_dir + '/odoo_update/files'
		
                    def rcopy(dirname, path):
                        d = os.listdir(dirname)
                        for f in d:
                            if os.path.isdir(dirname + '/' + f):						
                                if not os.path.isdir(path + '/' + f):
                                    #crear la carpeta
                                    try:
                                        os.mkdir(path + '/' + f)
                                    except:
                                        return False
                                if not rcopy(dirname + '/' + f, path + '/' + f):
                                    return False
                            else:						
                                #se hace una copia de seguridad del archivo
                                if os.path.isfile(path + '/' + f):
                                    try:
                                        shutil.copy(path + '/' +f, path + '/' +f + '.bak')
                                    except:
                                        #no se pudo hacer la copia de seguridad
                                        #retornar false
                                        return False
                                #se copia el archivo nuevo
                                try:
                                    shutil.copy(dirname + '/' + f, path + '/' + f)
                                except:
                                    #no se pudo copiar
                                    #retornar false
                                    #print("No se pudo copiar el archivo: "+ path + '/' + f)
                                    return False
                        return True
		
                    def rfiles(base_path, dirname):
                        files = []
                        d = os.listdir(dirname)
                        for f in d:
                            if os.path.isdir(dirname + '/' + f):
                                files+=rfiles(base_path, dirname + '/' + f)
                            else:
                                files.append((dirname + '/' +f)[len(base_path)+1:])
					
                        return files

                    def rrestore(dirname, path):
                        #restaurar todos los copiados
                        d = os.listdir(dirname)
                        for f in d:
                            if os.path.isdir(dirname + '/' + f):
                                if not rrestore(dirname + '/' + f, path + '/' + f):
                                    return False
                            else:
                                if os.path.isfile(path + '/' + f + '.bak'):
                                    try:
                                        shutil.copy(path + '/' + f + '.bak', path + '/' + f)
                                    except:
                                        return False
                                    try:
                                        os.unlink(path + '/' + f + '.bak')
                                    except:
                                        pass
                        return True

                    def rclean(dirname, path):
                        # borrar las salvas de seguridad
                        d = os.listdir(dirname)
                        for f in d:
                            if os.path.isdir(dirname+ '/' +f):
                                rclean(dirname + '/' + f, path + '/' + f)
                            else:
                                if os.path.isfile(path + '/' + f + '.bak'):
                                    os.unlink(path + '/' + f + '.bak')
                    
                    actual_path = __file__[0:-35]

                    # copiar los archivos contenidos en files
                    if not rcopy(files_directory, actual_path):
                        rrestore(files_directory, actual_path)
                        raise exceptions.Warning('No se pudo actualizar el sistema. Algunos archivos no pudieron copiarse por estar abiertos.')
                    else:
                        #se limpian las salvas de seguridad
                        rclean(files_directory, actual_path)
                    
                finally:
                    pass
        
        
        return install_modules, update_modules, restart_server, rescan_modules
    
    
    def case_restart(self):
        odoo.service.server.restart()

    
    def case_file_update(self):
        this = self[0]
        # read the file
        if not this.update_file:
            raise exceptions.Warning("You must upload a file")
        
        # verifiy the file contents
        zip_data = base64.decodestring(self.update_file)
        fp = BytesIO()
        fp.write(zip_data)
        try:
            res = this.import_file(fp)
        except Exception as e:
            raise e

        if res[3]:
            api.Environment.reset()
            odoo.modules.registry.Registry.new(this.env.cr.dbname, update_module=True)
        
        install_modules = res[0]
        for m in install_modules:
            mod = self.env['ir.module.module'].search([('name', '=', m)])
            mod.write({'state': 'to install'})

        update_modules = res[1]
        for m in update_modules:
            mod = self.env['ir.module.module'].search([('name', '=', m)])
            mod.write({'state': 'to upgrade'})
        
        this.env.cr.commit()

        if res[2]:
            this.write({'state': 'restart'})
            return {
                'type': 'ir.actions.act_window',
                'name': "Manual update",
                'res_model': 'res.updater',
                'view_mode': 'form',                
                'res_id': this.id,
                'views': [(False, 'form')],
                'target': 'new',
                'tag': 'reload',
            }
        else:
            api.Environment.reset()
            odoo.modules.registry.Registry.new(this.env.cr.dbname, update_module=True)
        
        this.write({'state': 'done'})
        return {
            'type': 'ir.actions.act_window',
            'name': "Manual update",
            'res_model': 'res.updater',
            'view_mode': 'form',            
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
            'tag': 'reload'
        }

    @api.model
    def _download_and_update(self):
        # connect to URL
        _logger.info('Checking for updates')
        # download and save in temp
        # extract and override
        
        # mark modules to install/update
        names_to_install = []
        modules = self.env['ir.module.module'].search([('name', 'in', names_to_install)])
        for m in modules:
            m.write({'state': 'to install'})
        
        names_to_update = [] #['tabax_flow']
        modules = self.env['ir.module.module'].search([('name', 'in', names_to_update)])
        for m in modules:
            m.write({'state': 'to upgrade'})
        
        self._cr.commit()
        # restart server
        _logger.warning('Restarting server to perform module upgrades')
        odoo.service.server.restart()

        return True

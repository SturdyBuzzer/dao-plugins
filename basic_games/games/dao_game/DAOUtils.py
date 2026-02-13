import mobase
import os
import re
import shutil
import struct
import xml.dom.minidom
import zipfile

from PyQt6.QtCore import qInfo, Qt
from PyQt6.QtWidgets import QMessageBox, QProgressDialog
from typing import Iterable
from xml.etree import ElementTree as ET

####################
### Helper Utils ###
####################
class DAOUtils:

    @staticmethod
    def setup_utils(organizer: mobase.IOrganizer, name: str):
        DAOUtils._organizer = organizer
        DAOUtils._plugin_name = name

    ###################
    ## Logging Utils ##
    ###################

    @staticmethod
    def log_message(message:str):
        if DAOUtils._organizer.pluginSetting(
            DAOUtils._plugin_name,
            "enable_logging",
        ): qInfo(f"[DAO] {message}")

    ####################
    ## Filetree Utils ##
    ####################    
    @staticmethod 
    def search_filetree(filetree: mobase.IFileTree, filename: str) -> list[str]:
        """Returns path of any files matching the filename."""
        result: list[str] = []
        for entry in DAOUtils.walk_tree(filetree):
            if not entry.isFile():
                continue
            if entry.name().casefold() != filename.casefold():
                continue
            file_path = entry.path()
            result.append(file_path)
        return result

    @staticmethod 
    def trim_branch(filetree: mobase.IFileTree) -> None:
        """Recursively trims empty IFileTree branch from top down"""
        if filetree.__len__():
            return
        parent = filetree.parent()
        filetree.detach()
        if parent is not None:
            DAOUtils.trim_branch(parent)

    @staticmethod 
    def walk_tree(filetree: mobase.IFileTree) -> Iterable[mobase.FileTreeEntry]:
        """Walk the IFileTree recursively (depth-first)."""
        stack: list[mobase.IFileTree] = [filetree]
        while stack:
            current = stack.pop()
            for entry in current:
                if entry.isDir() and isinstance(entry, mobase.IFileTree):
                    stack.append(entry)
                yield entry 

    ###############
    ## OS Utils ##
    ###############  
    @staticmethod 
    def copy_file(src: str, dst: str) -> bool:
        """"Copy src file to dst."""
        dir = os.path.dirname(dst)
        if not DAOUtils.make_dirs(dir):
            return False
        try:
            shutil.copy2(src, dst)
            return True 
        except Exception as e:
            DAOUtils.log_message(f"Failed to copy file {src} to {dst}: {e}.")    
            return False
    
    @staticmethod 
    def create_backup(src: str) -> bool:
        if not DAOUtils.file_exists(src):
            DAOUtils.log_message(f"Failed to create backup. File not found {src}")
            return False
        dst = f"{src}.mohidden"
        return DAOUtils.copy_file(src, dst)

    @staticmethod
    def create_link(target: str, link: str, force: bool) -> bool:
        """"Link src file to dst."""
        try:
            if os.path.lexists(link):
                if force:
                    os.remove(link)
                else:
                    DAOUtils.log_message(f"Failed to create link at {link}: File exists.")
                    return False
            try:
                os.symlink(target, link)
                DAOUtils.log_message(f"Created symlink: {link} -> {target}.")
            except OSError:
                os.link(target, link)
                DAOUtils.log_message(f"Created hard-link: {link} -> {target}.")
        except Exception as e:
            DAOUtils.log_message(f"Failed to create symlink {link} -> {target}: {e}.")
            return False
        return True
              
    @staticmethod 
    def extract_archive(src: str, dst: str, delete: bool = True) -> bool:
        """Extract archive at src to dst, and remove the archive if successful."""
        if not DAOUtils.make_dirs(dst):
            return False
        try:
            with zipfile.ZipFile(src, "r") as zip_ref:
                members = zip_ref.infolist()
                total = len(members)

                progress = QProgressDialog(f"Extracting {os.path.basename(src)}", None, 0, total)
                progress.setWindowModality(Qt.WindowModality.ApplicationModal)
                progress.setAutoClose(True)
                progress.setMinimumDuration(250)
                progress.setValue(0)

                for i, member in enumerate(members):
                    zip_ref.extract(member, dst)
                    progress.setValue(i + 1)
        except Exception as e:
            DAOUtils.log_message(f"Failed to extract archive {src} to {dst}: {e}.")
            return False
        return DAOUtils.remove_file(src) if delete else True

    @staticmethod
    def file_exists(file_path: str) -> bool:
        "Check if file exists at path"
        if os.path.exists(file_path):
            return os.path.isfile(file_path)
        return False
    
    @staticmethod 
    def get_ext(filename:str) -> str:
        return filename.rsplit(".", 1)[1]
    
    @staticmethod 
    def list_files(path: str) -> set[str]:
        """"List all files in a directory"""
        file_list: set[str] = set()
        if not os.path.isdir(path):
            return file_list
        for root, _, files in os.walk(path):
            for file in files:
                rel_path = os.path.relpath(root, path)
                file_path = DAOUtils.os_path(rel_path, file)
                file_list.add(file_path)
        return file_list    

    @staticmethod 
    def make_dirs(path: str) -> bool:
        """"Create dir at specified path."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to create dirs {path}: {e}.")
            return False

    @staticmethod 
    def move_file(src: str, dst: str) -> bool:
        """"Move src file to dst."""
        try:
            shutil.move(src, dst)
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to move file {src} to {dst}: {e}.")
            return False
           
    @staticmethod 
    def move_file_overwrite(src: str, dst: str) -> bool:
        """"Move src file to dst, with overwrite."""
        if not DAOUtils.remove_file(dst):
            return False
        return DAOUtils.move_file(src, dst)

    @staticmethod    
    def move_file_overwrite_dirs(src: str, dst: str) -> bool:
        """"Move src file to dst, with overwrite. Create dirs where necessary."""
        path = os.path.dirname(dst)
        if not DAOUtils.make_dirs(path):
            return False
        return DAOUtils.move_file_overwrite(src, dst)
        
    @staticmethod  
    def merge_dirs(src_dir: str, dst_dir: str) -> bool:
        """Move all files from src dir to dst dir recursively."""
        if not os.path.isdir(src_dir):
            DAOUtils.log_message(f"Failed to merge with {dst_dir} - Directory not found: {src_dir}.")
            return False
        for root, _, files in os.walk(src_dir):
            for file in files:
                rel_path = os.path.relpath(root, src_dir)
                src = DAOUtils.os_path(src_dir, rel_path, file)
                dst = DAOUtils.os_path(dst_dir, rel_path, file)
                if DAOUtils.move_file_overwrite_dirs(src, dst):
                    continue
                DAOUtils.log_message(f"Failed to merge files from {src_dir} to {dst_dir}.")
                return False
        return DAOUtils.remove_dir(src_dir)
    
    @staticmethod    
    def natural_sort_key(s: str):
        """key to help sort strings like Windows file explorer""" 
        return [
            int(text) if text.isdigit() else text.casefold()
            for text in re.split(r'(\d+)', s)
        ]
    
    @staticmethod 
    def os_path(*parts: str) -> str:
        """Return clean os path."""
        path = os.path.join(*parts)
        return os.path.normpath(path)
    
    @staticmethod 
    def os_path_casefold(*parts: str) -> str:
        """Return clean os path, lower case."""
        path = DAOUtils.os_path(*parts)
        return path.casefold()
    
    @staticmethod 
    def read_file(file_path: str) -> str:
        """Read file to string"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                return text
        except Exception as e:
            DAOUtils.log_message(f"Failed to read file {file_path}: {e}")
            return ""
    
    @staticmethod 
    def remove_file(file_path: str) -> bool:
        """Remove file at path."""
        if not DAOUtils.file_exists(file_path):
            return True
        try:
            os.unlink(file_path)
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to remove file {file_path}: {e}.")
            return False

    @staticmethod 
    def remove_dir(dir_path: str) -> bool:
        """Remove dir at path recursively."""
        if not os.path.isdir(dir_path):
            return True
        try:
            shutil.rmtree(dir_path)
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to remove dir {dir_path}: {e}")
            return False

    @staticmethod 
    def remove_empty_subdirs(dir_path: str) -> bool:
        """Remove all empty subdirectories under dir_path, recursively."""
        if not os.path.isdir(dir_path):
            return True
        result = True
        for root, dirs, _ in os.walk(dir_path, topdown=False):
            for dir in dirs:
                full_path = os.path.join(root, dir)
                if os.listdir(full_path):
                    continue
                try:
                    os.rmdir(full_path)
                except Exception as e:
                    DAOUtils.log_message(f"Failed to remove dir {full_path}: {e}")
                    result = False
        return result

    @staticmethod
    def remove_link(link: str, force: bool) -> bool:
        """"Remove link."""
        try:
            try:
                os.unlink(link)
                DAOUtils.log_message(f"Removed symlink: {link}.")
            except OSError:
                if force:
                    os.remove(link)
                    DAOUtils.log_message(f"Force-removed hard-link {link}.")
                else:
                    DAOUtils.log_message(f"Failed to remove link {link}: Not a valid symlink!")
                    return False
        except Exception as e:
            DAOUtils.log_message(f"Failed to remove link {link}: {e}.")
            return False
        return True
        
    @staticmethod 
    def restore_backup(dst: str) -> bool:
        src = f"{dst}.mohidden"
        if not DAOUtils.file_exists(src):
            return False
        return DAOUtils.move_file_overwrite(src, dst)
    
    @staticmethod 
    def search_dir(dir_name: str, filename: str) -> list[str]:
        """Search dir for files and return list of paths"""
        result: list[str] = []
        for root, _, files in os.walk(dir_name):
            for file in files:
                if file.casefold() != filename.casefold():
                    continue
                rel_path = os.path.relpath(root, dir_name)
                file_path = DAOUtils.os_path(dir_name, rel_path, file)
                result.append(file_path)
        return result
      
    @staticmethod 
    def touch_file(path: str) -> bool:
        """"Create file at path."""
        dir = os.path.dirname(path)
        if not DAOUtils.make_dirs(dir):
            return False
        try:
            open(path, 'a').close()
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to create file {path}: {e}.")
            return False
    
    @staticmethod 
    def write_file_bytes(file_path: str, file_content: bytes) -> bool:
        """Write bytes to file"""
        if not DAOUtils.touch_file(file_path):
            return False
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            return True
        except Exception as e:
            DAOUtils.log_message(f"Failed to write to file {file_path}: {e}")
            return False        
    
    
    ###############
    ## XML Utils ##
    ###############
    @staticmethod 
    def format_xml_file(xml_path: str) -> bool:
        """Rewrite XML file with formatted content."""
        xml_text = DAOUtils.read_file(xml_path)
        
        pretty_text = DAOUtils.pretty_format_xml(xml_text, "  ")
        if not pretty_text:
            return False

        return DAOUtils.write_file_bytes(xml_path, pretty_text)
       
    @staticmethod 
    def pretty_format_xml(xml_text: str, xml_indent: str = "  ") -> bytes:
        """Formats XML content with consistent indentation."""
        # Reduce white space between tags
        razed_text = re.sub(r">\s+<", "><", xml_text.strip())
        try:
             # Parse to doc and pretty format
            razed_doc = xml.dom.minidom.parseString(razed_text)
            pretty_bytes = razed_doc.toprettyxml(indent=xml_indent, encoding='utf-8', standalone=True)
            return pretty_bytes
        except Exception as e:
            DAOUtils.log_message(f"Failed to parse xml: {e}")
            return "".encode('utf-8')

    @staticmethod
    def overwrite_element(old_elem: ET.Element, new_elem: ET.Element) -> bool:
        """Fully overwrite an ElementTree element in-place."""
        # Overwrite tag
        old_elem.tag = new_elem.tag

        # Overwrite attributes completely
        old_elem.attrib.clear()
        old_elem.attrib.update(new_elem.attrib)

        # Overwrite text and tail
        old_elem.text = new_elem.text
        old_elem.tail = new_elem.tail

        # Overwrite children
        old_elem[:] = list(new_elem)

        return True

    @staticmethod 
    def read_file_xml(file_path: str) -> ET.Element | None:
        """Read xml file to ET element"""
        try:
            tree = ET.parse(file_path)
            return tree.getroot()
        except Exception as e:
            DAOUtils.log_message(f"Failed to read xml file {file_path}: {e}")
            return None   

    #################
    ## Misc. Utils ##
    #################
    @staticmethod
    def decode_bytes(data: bytes, encoding: str) -> str:
        """Decode a fixed-length byte string, trimming trailing nulls."""
        s = data.decode(encoding, errors="ignore")
        return s.rstrip("\0")

    @staticmethod
    def get_erf_paths(name: str, file_path: str) -> list[str]:
        """List files inside a DAO .erf archive."""
        file_list: list[str] = []
        try:
            with open(file_path, "rb") as f:
                # Header1 0-16
                hdr1 = f.read(16)
                file_type = DAOUtils.decode_bytes(hdr1[0:8], "utf-16le")
                version = DAOUtils.decode_bytes(hdr1[8:16], "utf-16le")
                if file_type != "ERF " or version not in ("V2.0", "V2.2"):
                    DAOUtils.log_message(f"ERF version not supported {file_type} {version}")
                    f.close()
                    return file_list
                # Header2 16-32 
                hdr2 = f.read(16)
                file_count, _, _, _ = struct.unpack("<4I", hdr2)
                # File List
                for _ in range(file_count):
                    entry_size = 76 if version == "V2.2" else 72
                    entry_data = f.read(entry_size)
                    name = DAOUtils.decode_bytes(entry_data[0:64], "utf-16le")
                    if not name:
                        continue
                    file_list.append(name)
        except Exception as e:
            DAOUtils.log_message(f"Failed to read ERF file {file_path}: {e}")
        return file_list 
    
    @staticmethod
    def show_message_box(
        header: str,
        message: str | list[str],
        link: str = "",
        link_name: str = "",
        cancel: bool = False,
        warning: bool = False,
        ) -> bool:
        """Generic message box with hyperlink option."""
        if isinstance(message, (list, tuple)):
            message_text = "<br>".join(message)
        else:
            message_text = message

        # Add link if provided
        if link and link_name:
            message_text += f'<br><a href="{link}">{link_name}</a>'

        icon = QMessageBox.Icon.Warning if warning else QMessageBox.Icon.Information
        box = QMessageBox()
        box.setWindowTitle(header)
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(message_text)
        box.setIcon(icon)
        box.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            if cancel else QMessageBox.StandardButton.Ok
        )
        box.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        result = box.exec()
        return result == QMessageBox.StandardButton.Ok
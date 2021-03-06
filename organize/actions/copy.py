import logging
import os
import shutil

from organize.utils import Path, fullpath, find_unused_filename

from .action import Action
from .trash import Trash


class Copy(Action):

    """
    Copy a file to a new location.
    If the specified path does not exist it will be created.

    :param str dest:
        The destination where the file should be copied to.
        If `dest` ends with a slash / backslash, the file will be copied into
        this folder and keep its original name.

    :param bool overwrite:
        specifies whether existing files should be overwritten.
        Otherwise it will start enumerating files (append a counter to the
        filename) to resolve naming conflicts. [Default: False]

    Examples:
        - Copy all pdfs into `~/Desktop/somefolder/` and keep filenames

          .. code-block:: yaml
            :caption: config.yaml

            rules:
              - folders: ~/Desktop
                filters:
                  - Extension: pdf
                actions:
                  - Copy: '~/Desktop/somefolder/'

        - Use a placeholder to copy all .pdf files into a "PDF" folder and all .jpg
          files into a "JPG" folder. Existing files will be overwritten.

          .. code-block:: yaml
            :caption: config.yaml

            rules:
              - folders: ~/Desktop
                filters:
                  - Extension:
                      - pdf
                      - jpg
                actions:
                  - Copy:
                      dest: '~/Desktop/{extension.upper}/'
                      overwrite: true

        - Copy into the folder `Invoices`. Keep the filename but do not
          overwrite existing files (adds an index to the file)

          .. code-block:: yaml
            :caption: config.yaml

            rules:
              - folders: ~/Desktop/Invoices
                filters:
                  - Extension:
                      - pdf
                actions:
                  - Copy:
                      dest: '~/Documents/Invoices/'
                      overwrite: false
    """

    def __init__(self, dest: str, overwrite=False):
        self.dest = dest
        self.overwrite = overwrite
        self.log = logging.getLogger(__name__)

    def run(self, attrs: dict, simulate: bool):
        path = attrs['path']
        basedir = attrs['basedir']

        expanded_dest = self.fill_template_tags(self.dest, attrs)
        # if only a folder path is given we append the filename to have the full
        # path. We use os.path for that because pathlib removes trailing slashes
        if expanded_dest.endswith(('\\', '/')):
            expanded_dest = os.path.join(expanded_dest, path.name)

        new_path = fullpath(expanded_dest)
        if new_path.exists() and not new_path.samefile(path):
            if self.overwrite:
                self.print('File already exists')
                Trash().run({'path': new_path}, simulate=simulate)
            else:
                new_path = find_unused_filename(new_path)

        self.print('Copy to "%s"' % new_path)
        if not simulate:
            self.log.info('Creating folder if not exists: %s', new_path.parent)
            new_path.parent.mkdir(parents=True, exist_ok=True)
            self.log.info('Copying "%s" to "%s"', path, new_path)
            shutil.copy2(src=str(path), dst=str(new_path))

        # the next actions should handle the original file
        return None

    def __str__(self):
        return 'Copy(dest=%s, overwrite=%s)' % (self.dest, self.overwrite)

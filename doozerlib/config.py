import metadata
import yaml
from pykwalify.core import Core
import os
import shutil
from pushd import Dir
import exectools
import sys


VALID_UPDATES = {
    'mode': metadata.CONFIG_MODES,
}


# Used in oit.py to print out valid update options
# in --help output
def valid_updates():
    res = '\n\tKey\tValid Options\n\n'
    for k, v in VALID_UPDATES.iteritems():
        opts = ""
        if v:
            v = [str(i) for i in v]
            opts = ':\t{}'.format(','.join(v))
        res += '\t{}{}\n\n'.format(k, opts)
    return res


class MetaDataConfig(object):
    """
    Holds common functions for managing the MetaData configs
    Mostly is a class to hold runtime
    """
    def __init__(self, runtime):
        self.runtime = runtime
        if self.runtime.remove_tmp_working_dir:
            print('config:* options require a non-temporary working space. Must run with --working-dir')
            sys.exit(1)

    def update_meta(self, meta, k, v):
        """
        Convenience function for setting meta keys
        """
        self.runtime.logger.info('{}: [{}] -> {}'.format(meta.config_filename, k, v))
        meta.config[k] = v
        print(meta.config)
        print(meta.data_obj.data)
        meta.save()

    def delete_key(self, meta, k):
        """
        Convenience function for deleting meta keys
        """

        self.runtime.logger.info('{}: Delete [{}]'.format(meta.config_filename, k, ))
        meta.config.pop(k, None)
        meta.save()

    def update(self, key, val):
        """
        Update [key] to [val] in all given image/rpm metas
        VALID_UPDATES is used to lock out what can be updated
        Right now only [mode] is valid, but that may change
        """
        if key not in VALID_UPDATES:
            raise ValueError('{} is not a valid update key. See --help'.format(key))

        if VALID_UPDATES[key]:
            if val not in VALID_UPDATES[key]:
                msg = '{} is not a valid value for {}. Use one of: {}'.format(val, key, ','.join(VALID_UPDATES[key]))
                raise ValueError(msg)

        for img in self.runtime.image_metas():
            self.update_meta(img, key, val)

        for rpm in self.runtime.rpm_metas():
            self.update_meta(rpm, key, val)

    def config_print(self, key=None, name_only=False, as_yaml=False):
        """
        Print name, sub-key, or entire config
        """

        data = dict(images={}, rpms={})

        def _collect_data(metas, output):
            for meta in metas:
                if name_only:
                    entry = meta.config_filename
                elif key:
                    entry = meta.config.get(key, None)
                else:
                    entry = meta.config.primitive()
                output[meta.config_filename.replace('.yml', '')] = entry

        _collect_data(self.runtime.image_metas(), data["images"])
        _collect_data(self.runtime.rpm_metas(), data["rpms"])

        if as_yaml:
            print(yaml.safe_dump(data, default_flow_style=False))
            return

        def _do_print(kind, output):
            if not output:
                return
            print('')
            print('********* {} *********'.format(kind))
            for name, entry in output.iteritems():
                if name_only:
                    print(entry)
                else:
                    print("*****{}.yml*****".format(name))
                    print(yaml.safe_dump(entry, default_flow_style=False))
                    print('')

        _do_print("Images", data['images'])
        _do_print(" RPMS ", data['rpms'])

    def commit(self, msg):
        """
        Commit outstanding metadata config changes
        """
        self.gitdata.commit()

    def push(self):
        """
        Push changes back to config repo.
        Will of course fail if user does not have write access.
        """
        self.gitdata.push()

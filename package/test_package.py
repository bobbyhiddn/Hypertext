#!/usr/bin/env python3
"""Test script to verify hypertext package imports work correctly."""

import sys
sys.path.insert(0, '.')

def main():
    # Test basic package import
    print('Testing hypertext package...')
    import hypertext
    print(f'  hypertext version: {hypertext.__version__}')

    # Test gemini subpackage
    print('Testing hypertext.gemini...')
    from hypertext.gemini import text, image, style
    print('  text, image, style modules OK')

    # Test cards subpackage
    print('Testing hypertext.cards...')
    from hypertext.cards import render, composite, clean, validate
    print('  render, composite, clean, validate modules OK')

    # Test watermark subpackage
    print('Testing hypertext.watermark...')
    from hypertext.watermark import crypto, apply, verify
    print('  crypto, apply, verify modules OK')

    # Test lots subpackage
    print('Testing hypertext.lots...')
    from hypertext.lots import generation, renderer, exporter
    print('  generation, renderer, exporter modules OK')

    # Test gallery subpackage
    print('Testing hypertext.gallery...')
    from hypertext.gallery import builder, deck
    print('  builder, deck modules OK')

    # Test utils subpackage
    print('Testing hypertext.utils...')
    from hypertext.utils import image as img_utils
    print('  image module OK')

    # Test CLI
    print('Testing hypertext.cli...')
    from hypertext.cli import cli
    print('  cli module OK')

    print()
    print('All package imports successful!')
    return 0


if __name__ == "__main__":
    sys.exit(main())

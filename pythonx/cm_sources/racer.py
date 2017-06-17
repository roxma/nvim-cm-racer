# -*- coding: utf-8 -*-

# For debugging, use this command to start neovim:
#
# NVIM_PYTHON_LOG_FILE=nvim.log NVIM_PYTHON_LOG_LEVEL=INFO nvim
#
#
# Please register source before executing any other code, this allow cm_core to
# read basic information about the source without loading the whole module, and
# modules required by this module
from cm import register_source, getLogger, Base

register_source(name='racer',
                priority=9,
                abbreviation='rs',
                word_pattern=r'[\w/]+',
                scoping=True,
                scopes=['rust'],
                early_cache=1,
                cm_refresh_patterns=[r'\.$', r'::$'],)

import json
import os
import subprocess
import glob

logger = getLogger(__name__)


class Source(Base):

    def __init__(self, nvim):
        super(Source, self).__init__(nvim)

        # dependency check
        try:
            from distutils.spawn import find_executable
            if not find_executable("racer"):
                self.message('error', 'Can not find racer for completion, you need https://github.com/phildawes/racer' )
            if not self._check_rust_src_path():
                self.message('error', '$RUST_SRC_PATH not defined, please read https://github.com/phildawes/racer#configuration' )
        except Exception as ex:
            logger.exception(ex)

    def _check_rust_src_path(self):
        if "RUST_SRC_PATH" in os.environ:
            return os.environ["RUST_SRC_PATH"]
        # auto detect, if user already run `rustup component add rust-src`
        found = glob.glob(os.path.expanduser(
            "~/.rustup/toolchains/*/lib/rustlib/src/rust/src"))
        if len(found) == 1:
            logger.info("detect RUST_SRC_PATH as [%s]", found[0])
            os.environ["RUST_SRC_PATH"] = found[0]
            return found[0]
        return None

    def cm_refresh(self, info, ctx, *args):

        src = self.get_src(ctx).encode('utf-8')
        lnum = ctx['lnum']
        col = ctx['col']
        filepath = ctx['filepath']
        startcol = ctx['startcol']

        args = ['racer', 'complete-with-snippet', str(lnum), str(col - 1), filepath, '-']
        proc = subprocess.Popen(args=args,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)

        result, errs = proc.communicate(src, timeout=30)

        logger.debug("args: %s, result: [%s]", args, result.decode())

        lines = result.decode('utf-8').splitlines()

        # typical output example:
        #   PREFIX 47,51,Stri
        #   MATCH String;String;263;11;/data/roxma/.multirust/toolchains/stable-x86_64-unknown-linux-gnu/lib/rustlib/src/rust/src/libstd/../libcollections/string.rs;Struct;pub struct String;"A UTF-8 encoded, growable string.\n\nThe `String` type is the most common string type that has ownership over the\ncontents of the string. It has a close relationship with its borrowed\ncounterpart, the primitive [`str`].\n\n[`str`]: ../../std/primitive.str.html\n\n# Examples\n\nYou can create a `String` from a literal string with `String::from`:\n\n```\nlet hello = String::from(\"Hello, world!\")\;\n```\n\nYou can append a [`char`] to a `String` with the [`push()`] method, and\nappend a [`&str`] with the [`push_str()`] method:\n\n```\nlet mut hello = String::from(\"Hello, \")\;\n\nhello.push(\'w\')\;\nhello.push_str(\"orld!\")\;\n```\n\n[`char`]: ../../std/primitive.char.html\n[`push()`]: #method.push\n[`push_str()`]: #method.push_str\n\nIf you have a vector of UTF-8 bytes, you can create a `String` from it with\nthe [`from_utf8()`] method:\n\n```\n// some bytes, in a vector\nlet sparkle_heart = vec![240, 159, 146, 150]\;\n\n// We know these bytes are valid, so we\'ll use `unwrap()`.\nlet sparkle_heart = String::from_utf8(sparkle_heart).unwrap()\;\n\nassert_eq!(\"💖\", sparkle_heart)\;\n```\n\n[`from_utf8()`]: #method.from_utf8\n\n# UTF-8\n\n`String`s are always valid UTF-8. This has a few implications, the first of\nwhich is that if you need a non-UTF-8 string, consider [`OsString`]. It is\nsimilar, but without the UTF-8 constraint. The second implication is that\nyou cannot index into a `String`:\n\n```ignore\nlet s = \"hello\"\;\n\nprintln!(\"The first letter of s is {}\", s[0])\; // ERROR!!!\n```\n\n[`OsString`]: ../../std/ffi/struct.OsString.html\n\nIndexing is intended to be a constant-time operation, but UTF-8 encoding\ndoes not allow us to do this. Furthermore, it\'s not clear what sort of\nthing the index should return: a byte, a codepoint, or a grapheme cluster.\nThe [`bytes()`] and [`chars()`] methods return iterators over the first\ntwo, respectively.\n\n[`bytes()`]: #method.bytes\n[`chars()`]: #method.chars\n\n# Deref\n\n`String`s implement [`Deref`]`<Target=str>`, and so inherit all of [`str`]\'s\nmethods. In addition, this means that you can pass a `String` to any\nfunction which takes a [`&str`] by using an ampersand (`&`):\n\n```\nfn takes_str(s: &str) { }\n\nlet s = String::from(\"Hello\")\;\n\ntakes_str(&s)\;\n```\n\n[`&str`]: ../../std/primitive.str.html\n[`Deref`]: ../../std/ops/trait.Deref.html\n\nThis will create a [`&str`] from the `String` and pass it in. This\nconversion is very inexpensive, and so generally, functions will accept\n[`&str`]s as arguments unless they need a `String` for some specific reason.\n\n\n# Representation\n\nA `String` is made up of three components: a pointer to some bytes, a\nlength, and a capacity. The pointer points to an internal buffer `String`\nuses to store its data. The length is the number of bytes currently stored\nin the buffer, and the capacity is the size of the buffer in bytes. As such,\nthe length will always be less than or equal to the capacity.\n\nThis buffer is always stored on the heap.\n\nYou can look at these with the [`as_ptr()`], [`len()`], and [`capacity()`]\nmethods:\n\n```\nuse std::mem\;\n\nlet story = String::from(\"Once upon a time...\")\;\n\nlet ptr = story.as_ptr()\;\nlet len = story.len()\;\nlet capacity = story.capacity()\;\n\n// story has nineteen bytes\nassert_eq!(19, len)\;\n\n// Now that we have our parts, we throw the story away.\nmem::forget(story)\;\n\n// We can re-build a String out of ptr, len, and capacity. This is all\n// unsafe because we are responsible for making sure the components are\n// valid:\nlet s = unsafe { String::from_raw_parts(ptr as *mut _, len, capacity) } \;\n\nassert_eq!(String::from(\"Once upon a time...\"), s)\;\n```\n\n[`as_ptr()`]: #method.as_ptr\n[`len()`]: #method.len\n[`capacity()`]: #method.capacity\n\nIf a `String` has enough capacity, adding elements to it will not\nre-allocate. For example, consider this program:\n\n```\nlet mut s = String::new()\;\n\nprintln!(\"{}\", s.capacity())\;\n\nfor _ in 0..5 {\n    s.push_str(\"hello\")\;\n    println!(\"{}\", s.capacity())\;\n}\n```\n\nThis will output the following:\n\n```text\n0\n5\n10\n20\n20\n40\n```\n\nAt first, we have no memory allocated at all, but as we append to the\nstring, it increases its capacity appropriately. If we instead use the\n[`with_capacity()`] method to allocate the correct capacity initially:\n\n```\nlet mut s = String::with_capacity(25)\;\n\nprintln!(\"{}\", s.capacity())\;\n\nfor _ in 0..5 {\n    s.push_str(\"hello\")\;\n    println!(\"{}\", s.capacity())\;\n}\n```\n\n[`with_capacity()`]: #method.with_capacity\n\nWe end up with a different output:\n\n```text\n25\n25\n25\n25\n25\n25\n```\n\nHere, there\'s no need to allocate more memory inside the loop."
        #   END
        # another example(`String::`)
        #   PREFIX 55,55,
        #   MATCH new;new();352;11;/data/roxma/.multirust/toolchains/stable-x86_64-unknown-linux-gnu/lib/rustlib/src/rust/src/libstd/../libcollections/string.rs;Function;pub fn new() -> String;"Creates a new empty `String`.\n\nGiven that the `String` is empty, this will not allocate any initial\nbuffer. While that means that this initial operation is very\ninexpensive, but may cause excessive allocation later, when you add\ndata. If you have an idea of how much data the `String` will hold,\nconsider the [`with_capacity()`] method to prevent excessive\nre-allocation.\n\n[`with_capacity()`]: #method.with_capacity\n\n# Examples\n\nBasic usage:\n\n```\nlet s = String::new()\;\n```"
        #   MATCH with_capacity;with_capacity(${1:capacity});395;11;/data/roxma/.multirust/toolchains/stable-x86_64-unknown-linux-gnu/lib/rustlib/src/rust/src/libstd/../libcollections/string.rs;Function;pub fn with_capacity(capacity: usize) -> String;"Creates a new empty `String` with a particular capacity.\n\n`String`s have an internal buffer to hold their data. The capacity is\nthe length of that buffer, and can be queried with the [`capacity()`]\nmethod. This method creates an empty `String`, but one with an initial\nbuffer that can hold `capacity` bytes. This is useful when you may be\nappending a bunch of data to the `String`, reducing the number of\nreallocations it needs to do.\n\n[`capacity()`]: #method.capacity\n\nIf the given capacity is `0`, no allocation will occur, and this method\nis identical to the [`new()`] method.\n\n[`new()`]: #method.new\n\n# Examples\n\nBasic usage:\n\n```\nlet mut s = String::with_capacity(10)\;\n\n// The String contains no chars, even though it has capacity for more\nassert_eq!(s.len(), 0)\;\n\n// These are all done without reallocating...\nlet cap = s.capacity()\;\nfor i in 0..10 {\n    s.push(\'a\')\;\n}\n\nassert_eq!(s.capacity(), cap)\;\n\n// ...but this may make the vector reallocate\ns.push(\'a\')\;\n```"
        #   END
        matches = []
        for line in lines:

            fields = line.split(";")
            tword = fields[0].split(' ')

            if tword[0] != "MATCH":
                if tword == "prefix":
                    startcol = col - len(fields[2].encode())
                continue

            t, word = tword

            match = dict(word=word)

            menu = fields[6]
            if "RUST_SRC_PATH" in os.environ and menu.startswith(os.environ["RUST_SRC_PATH"]):
                menu = menu[len(os.environ["RUST_SRC_PATH"]):]

            match['menu'] = menu

            snippet = fields[1]
            if snippet != word:
                match['snippet'] = snippet

            matches.append(match)

        logger.info("matches: [%s]", matches)

        self.complete(info, ctx, startcol, matches)

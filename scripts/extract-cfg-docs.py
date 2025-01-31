#!/usr/bin/env python
# dist: public

import sys, re, string, glob

re_cfghelp = re.compile(r"(/\*|#) cfghelp: (.*?):(.*?), (.*)$")
re_crap = re.compile(r'(\*|#) (.*?) ?(\*/)?$')


def rem_crap(l):
	m = re_crap.match(l)
	if m:
		return m.group(2)
	else:
		return l


def get_type(attrs):
	for t, n in [
		('int', 'Integer'),
		('bool', 'Boolean'),
		('boolean', 'Boolean'),
		('string', 'String'),
		('enum', 'Enumerated')]:
		if t in attrs:
			return n
	return 'Other'

def get_field(attrs, fld):
	fld = '%s:' % fld
	for a in attrs:
		if a.startswith(fld):
			a = a[len(fld):]
			return a.strip()
	return None


def fix_latex(line):
	if not line:
		return line
	line = line.replace('<', '\\lt{}')
	line = line.replace('>', '\\gt{}')
	line = line.replace('_', '\\_')
	line = line.replace('#', '\\#')
	line = line.replace('$', '\\$')
	line = line.replace('^', '\\^')
	line = line.replace('%', '\\%')
	return line

def print_latex_1(docs, what):
	for sec, keys in docs:
		sec = fix_latex(sec)
		for key, (attrs, text) in keys:
			ok = 0
			if what:
				if attrs[0] == what: ok = 1
			else:
				if attrs[0] != 'global' and attrs[0] != 'arena': ok = 1
			if ok:
				df = fix_latex(get_field(attrs, 'def'))
				range = fix_latex(get_field(attrs, 'range'))
				mod = fix_latex(get_field(attrs, 'mod'))
				tp = get_type(attrs)

				if tp == 'Boolean':
					if df == '1':
						df = 'Yes'
					elif df == '0':
						df = 'No'

				print('\\setting{%s}{%s}' % (sec, key))
				if not what:
					print('\\settingfile{%s}' % fix_latex(attrs[0]))
				print('\\settingtype{%s}' % tp)
				if mod != None:
					print('\\requiremod{%s}' % mod)
				if df != None:
					print('\\settingdefault{%s}' % df)
				if range != None:
					print('\\settingrange{%s}' % range)
				print(fix_latex(text))
				print()

def print_latex(docs):
	# first global
	print('\n\\subsection{Global settings}\n')
	print_latex_1(docs, 'global')
	print('\n\\subsection{Arena settings}\n')
	print_latex_1(docs, 'arena')
	print('\n\\subsection{Other settings}\n')
	print_latex_1(docs, None)


def print_c(docs):
	def c(s):
		if s:
			return '"%s"' % s
		else:
			return 'NULL'

	print('/* this file was automatically generated by extract-cfg-docs.py */')
	print()
	print('#include "cfghelp.h"')
	print()

	ss = []
	secnames = []
	for sec, keys in docs:

		print('static const struct key_help cfg_help_section_contents_%s[] =\n{' % sec)

		keynames = []
		for key, (attrs, txt) in keys:

			if attrs[0] == 'arena':
				loc = 'Arena'
			elif attrs[0] == 'global':
				loc = 'Global'
			else:
				loc = 'File: %s' % attrs[0]

			df = c(get_field(attrs, 'def'))
			range = c(get_field(attrs, 'range'))
			mod = c(get_field(attrs, 'mod'))
			tp = get_type(attrs)

			print('\t{ "%s", "%s", "%s", %s, %s, %s,\n\t\t"%s" },' % (key, loc, tp, range, mod, df, txt))
			keynames.append(key)

		print('};\n')
		ss.append('\t{ "%s", %d, cfg_help_section_contents_%s,\n\t\t"%s" },' % \
			(sec, len(keys), sec, ', '.join(keynames)))
		secnames.append(sec)

	print("\n\nstatic const struct section_help cfg_help_sections[] =\n{")
	for s in ss:
		print(s)
	print('};')

	#print "\nstatic const int cfg_help_section_count = %d;" % len(docs)
	print("\n#define cfg_help_section_count %d" % len(docs))

	print('\nstatic const char cfg_help_all_section_names[] = "%s";' % \
		', '.join(secnames))

	print("\n\n/* end of generated code */\n")


def extract_docs(lines):
	docs = {}
	i = 0
	while i < len(lines):
		l = lines[i]
		i = i + 1

		m = re_cfghelp.search(l)
		if m:
			cmtchar, sec, key, attrs = m.groups()
			while attrs.endswith('\\'):
				attrs = attrs[:-1] + rem_crap(lines[i])
				i = i + 1
			text = []
			while (cmtchar == '#' and lines[i].startswith('#')) or \
			      (cmtchar != '#' and not lines[i].endswith('*/')):
				text.append(lines[i])
				i = i + 1
			if cmtchar != '#':
				text.append(lines[i])
				i = i + 1

			text = ' '.join(map(rem_crap, text))
			attrs = list(map(lambda x: x.strip(), attrs.split(',')))

			if sec not in docs: docs[sec] = {}
			docs[sec][key] = (attrs, text)

	return docs


def mycmp(a,b):
	ak, av = a
	bk, bv = b
	return cmp(ak.lower(), bk.lower())

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print("You must specify either -c or -l.")
	else:
		# open output
		sys.stdout = open(sys.argv[2], 'w')

		# get input
		lines = []
		for pat in sys.argv[3:]:
			for f in glob.glob(pat):
				lines.extend(list(map(lambda x: x.strip(), open(f).readlines())))
		docs = extract_docs(lines)

		# sort
		di = list(docs.items())
		docs = []
		for s, ks in di:
			ks = list(ks.items())
			#ks.sort(mycmp)
			sorted(ks)
			docs.append((s, ks))
		#docs.sort(mycmp)
		sorted(docs)

		# print
		if sys.argv[1] == '-c':
			print_c(docs)
		elif sys.argv[1] == '-l':
			print_latex(docs)
		else:
			print("unknown option")
			sys.exit(1)


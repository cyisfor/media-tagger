#include "parseui.xml.h"
#include "squeetie.png.h"
#include "sweetie_thinking.gif.h"

#include <Python.h>
#include <gtk/gtk.h>
#include <assert.h>

PyObject* Error = NULL;

static void ignore_result(PyObject* result) {
	Py_XDECREF(result);
}

static void button_clicked(GtkWidget* widget, GdkEventButton* event,
													 PyObject* on_clicked) {
	PyObject* arglist = Py_BuildValue
		("(iii)",
		 event->type, event->state, event->button);
	ignore_result(PyObject_CallObject(on_clicked, arglist));
	Py_DECREF(arglist);
}

static void destroyed(GtkWidget* widget,
											PyObject* on_destroyed) {
	ignore_result(PyObject_CallObject(on_destroyed,NULL));
}

typedef struct ui {
	GtkImage* img;
	GdkPixbufAnimation* ready;
	GdkPixbufAnimation* thinking;
} *ui;

static GdkPixbufAnimation* load_icon(unsigned char* buf, gsize len) {
	GdkPixbufLoader* loader = gdk_pixbuf_loader_new();
	gdk_pixbuf_loader_set_size(loader, 32, 32);
	GError* error = NULL;
	gdk_pixbuf_loader_write(loader, buf,len,&error);
	assert(error==NULL);
	gdk_pixbuf_loader_close(loader,&error);
	GdkPixbufAnimation* anim = gdk_pixbuf_loader_get_animation(loader);
	g_object_unref(loader);
	return anim;
}

static PyObject* save_callback(PyObject* cb) {
	assert(PyCallable_Check(cb));
	Py_INCREF(cb);
	return cb;
}

void free_capsule(PyObject* c) {
	g_free(PyCapsule_GetPointer(c,"_parseui.UI"));
	Py_DECREF(c);
}

static PyObject* load(PyObject* self, PyObject* args) {
	PyObject* on_clicked=NULL, *on_destroyed=NULL;
	assert(PyArg_ParseTuple(args,"(OO)",&on_clicked,&on_destroyed));
	on_clicked = save_callback(on_clicked);
	on_destroyed = save_callback(on_destroyed);
	
	GtkBuilder* b = gtk_builder_new_from_string((const char*)parseui, parseui_size);
	GtkWidget* top = GTK_WIDGET(gtk_builder_get_object(b,"top"));
	g_signal_connect(top, "button_release_event", (GCallback)button_clicked,
									 on_clicked);
	g_signal_connect(top, "destroy", (GCallback)destroyed,
									 on_destroyed);
	gtk_widget_show_all(top);
	ui ui = g_new(struct ui, 1);
	ui->img = GTK_IMAGE(gtk_builder_get_object(b,"image"));
	ui->ready = load_icon(squeetie,squeetie_size);
	ui->thinking = load_icon(sweetie_thinking, sweetie_thinking_size);

	return PyCapsule_New(ui, "_parseui.UI", free_capsule);
}

enum states { READY = 0, THINKING = 1 };

static PyObject* state(PyObject* self, PyObject* args) {
	PyObject* pui = NULL;
	enum states state = READY;
	assert(PyArg_ParseTuple(args,"(Oi)",&pui,&state));
	ui ui = (struct ui*) PyCapsule_GetPointer(pui, "_parseui.UI");
	switch(state) {
	#define CASE(name,mem) \
		case name: \
			gtk_image_set_from_animation \
				(ui->img, \
				 ui->mem); \
			break
		CASE(READY,ready);
		CASE(THINKING,thinking);
	};
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef Methods[] = {
    {"load",  load, METH_VARARGS,
     "Load ui."},
		{"state", state, METH_VARARGS,
		 "Set ui state"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef module = {
   PyModuleDef_HEAD_INIT,
   "_parseui",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   Methods
};

PyMODINIT_FUNC
PyInit__parseui(void) {
	PyObject* m = PyModule_Create(&module);	
  if (m == NULL)
		return NULL;
	
	Error = PyErr_NewException("_parseui.error", NULL, NULL);
	Py_INCREF(Error);
	PyModule_AddObject(m, "error", Error);
	return m;
}

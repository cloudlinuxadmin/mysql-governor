#include <libxml/xmlmemory.h>

xmlFreeFunc xmlFree = (xmlFreeFunc) free;
xmlMallocFunc xmlMalloc = (xmlMallocFunc) malloc;
xmlMallocFunc xmlMallocAtomic = (xmlMallocFunc) malloc;
xmlReallocFunc xmlRealloc = (xmlReallocFunc) realloc;
xmlStrdupFunc xmlMemStrdup = (xmlStrdupFunc) strdup;

static xmlParserInputPtr
xmlDefaultExternalEntityLoader(const char *URL, const char *ID,
                               xmlParserCtxtPtr ctxt)
{
    //TODO:
    return NULL;
}

static xmlExternalEntityLoader xmlCurrentExternalEntityLoader =
       xmlDefaultExternalEntityLoader;


int
xmlKeepBlanksDefault(int val) {
    return 0;
}

int
xmlInitParserCtxt(xmlParserCtxtPtr ctxt)
{
    // TODO: Mock it?
    return 0;
}

static int xmlNoNetExists(const char *URL) {
    const char *path;

    if (URL == NULL)
            return(0);

    if (!xmlStrncasecmp(BAD_CAST URL, BAD_CAST "file://localhost/", 17))
        path = &URL[16];
    else if (!xmlStrncasecmp(BAD_CAST URL, BAD_CAST "file:///", 8)) {
        path = &URL[7];
    } else
        path = URL;
    return 0; // TODO: xmlCheckFilename(path);
}

xmlParserInputPtr
xmlLoadExternalEntity(const char *URL, const char *ID, xmlParserCtxtPtr ctxt) {
    if ((URL != NULL) && (xmlNoNetExists(URL) == 0)) {
        char *canonicFilename;
        xmlParserInputPtr ret;

        canonicFilename = (char *) xmlCanonicPath((const xmlChar *) URL);
        if (canonicFilename == NULL) {
            return(NULL);
        }
        ret = xmlCurrentExternalEntityLoader(canonicFilename, ID, ctxt);
        xmlFree(canonicFilename);
        return(ret);
    }
    return(xmlCurrentExternalEntityLoader(URL, ID, ctxt));
}

void
xmlFreeParserCtxt(xmlParserCtxtPtr ctxt)
{
    xmlParserInputPtr input;

    if (ctxt == NULL) return;

// TODO: Mock it?
#if 0
    while ((input = inputPop(ctxt)) != NULL) { /* Non consuming */
        xmlFreeInputStream(input);
    }
#endif
    if (ctxt->spaceTab != NULL) xmlFree(ctxt->spaceTab);
    if (ctxt->nameTab != NULL) xmlFree((xmlChar * *)ctxt->nameTab);
    if (ctxt->nodeTab != NULL) xmlFree(ctxt->nodeTab);
    if (ctxt->nodeInfoTab != NULL) xmlFree(ctxt->nodeInfoTab);
    if (ctxt->inputTab != NULL) xmlFree(ctxt->inputTab);
    if (ctxt->version != NULL) xmlFree((char *) ctxt->version);
    if (ctxt->encoding != NULL) xmlFree((char *) ctxt->encoding);
    if (ctxt->extSubURI != NULL) xmlFree((char *) ctxt->extSubURI);
    if (ctxt->extSubSystem != NULL) xmlFree((char *) ctxt->extSubSystem);
/*
#ifdef LIBXML_SAX1_ENABLED
    if ((ctxt->sax != NULL) &&
        (ctxt->sax != (xmlSAXHandlerPtr) &xmlDefaultSAXHandler))
#else
*/
    if (ctxt->sax != NULL)
/*
#endif // LIBXML_SAX1_ENABLED
*/
        xmlFree(ctxt->sax);
    if (ctxt->directory != NULL) xmlFree((char *) ctxt->directory);
    if (ctxt->vctxt.nodeTab != NULL) xmlFree(ctxt->vctxt.nodeTab);
    if (ctxt->atts != NULL) xmlFree((xmlChar * *)ctxt->atts);
    if (ctxt->dict != NULL) xmlDictFree(ctxt->dict);
    if (ctxt->nsTab != NULL) xmlFree((char *) ctxt->nsTab);
    if (ctxt->pushTab != NULL) xmlFree(ctxt->pushTab);
    if (ctxt->attallocs != NULL) xmlFree(ctxt->attallocs);
    if (ctxt->attsDefault != NULL)
        xmlHashFree(ctxt->attsDefault, (xmlHashDeallocator) xmlFree);
    if (ctxt->attsSpecial != NULL)
        xmlHashFree(ctxt->attsSpecial, NULL);
    if (ctxt->freeElems != NULL) {
        xmlNodePtr cur, next;

        cur = ctxt->freeElems;
        while (cur != NULL) {
            next = cur->next;
            xmlFree(cur);
            cur = next;
        }
    }
    if (ctxt->freeAttrs != NULL) {
        xmlAttrPtr cur, next;

        cur = ctxt->freeAttrs;
        while (cur != NULL) {
            next = cur->next;
            xmlFree(cur);
            cur = next;
        }
    }
    if (ctxt->lastError.message != NULL)
        xmlFree(ctxt->lastError.message);
    if (ctxt->lastError.file != NULL)
        xmlFree(ctxt->lastError.file);
    if (ctxt->lastError.str1 != NULL)
        xmlFree(ctxt->lastError.str1);
    if (ctxt->lastError.str2 != NULL)
        xmlFree(ctxt->lastError.str2);
    if (ctxt->lastError.str3 != NULL)
        xmlFree(ctxt->lastError.str3);
/*
#ifdef LIBXML_CATALOG_ENABLED
    if (ctxt->catalogs != NULL)
        xmlCatalogFreeLocal(ctxt->catalogs);
#endif
*/
    xmlFree(ctxt);
}

xmlParserCtxtPtr
xmlNewParserCtxt(void)
{
    xmlParserCtxtPtr ctxt;

    ctxt = (xmlParserCtxtPtr) xmlMalloc(sizeof(xmlParserCtxt));
    if (ctxt == NULL) {
        return(NULL);
    }
    memset(ctxt, 0, sizeof(xmlParserCtxt));
    if (xmlInitParserCtxt(ctxt) < 0) {
        xmlFreeParserCtxt(ctxt);
        return(NULL);
    }
    return(ctxt);
}

xmlParserCtxtPtr
xmlCreateURLParserCtxt(const char *filename, int options)
{
    xmlParserCtxtPtr ctxt;
    xmlParserInputPtr inputStream;
    char *directory = NULL;

    ctxt = xmlNewParserCtxt();
    if (ctxt == NULL) {
        return(NULL);
    }

    if (options)
        xmlCtxtUseOptionsInternal(ctxt, options, NULL);
    ctxt->linenumbers = 1;

    inputStream = xmlLoadExternalEntity(filename, NULL, ctxt);
    if (inputStream == NULL) {
        xmlFreeParserCtxt(ctxt);
        return(NULL);
    }

    inputPush(ctxt, inputStream);
    if ((ctxt->directory == NULL) && (directory == NULL))
        directory = xmlParserGetDirectory(filename);
    if ((ctxt->directory == NULL) && (directory != NULL))
        ctxt->directory = directory;

    return(ctxt);
}

xmlDocPtr
xmlReadFile(const char *filename, const char *encoding, int options)
{
    xmlParserCtxtPtr ctxt;

    ctxt = xmlCreateURLParserCtxt(filename, options);
    if (ctxt == NULL)
        return (NULL);
    return (xmlDoRead(ctxt, NULL, encoding, options, 0));
}

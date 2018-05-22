/*
 * wrappers.h
 *
 *  Created on: Jun 7, 2012
 *      Author: alexey
 */

#ifndef WRAPPERS_H_
#define WRAPPERS_H_

#define GOVERNOR_READ_TIMEOUT 30

size_t fread_wrapper(void *__restrict __ptr, size_t __size, size_t __n, FILE * __restrict __stream);
size_t fwrite_wrapper(__const void *__restrict __ptr, size_t __size, size_t __n, FILE * __restrict __s);

#endif /* WRAPPERS_H_ */

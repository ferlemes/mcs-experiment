/*
 * Copyright 2020, Fernando Lemes da Silva
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package br.com.milliways.sample.rest;

import static org.springframework.web.bind.annotation.RequestMethod.DELETE;
import static org.springframework.web.bind.annotation.RequestMethod.GET;
import static org.springframework.web.bind.annotation.RequestMethod.POST;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * The endpoint to perform some operations on a customer database.
 */
@RestController
public class CustomerController {

    /**
     * The logger for this controller.
     */
    private static final Logger LOGGER = LoggerFactory.getLogger(CustomerController.class);

    /**
     * Handle POST requests to /customer endpoint.
     *
     * @return an HTTP OK response.
     */
    @RequestMapping(method = POST, path = "/customer")
    public ResponseEntity<String> addCustomer() {
        LOGGER.info("Adding new customer.");
        return ResponseEntity.ok("");
    }

    /**
     * Handle GET requests to /customer endpoint.
     *
     * @return an HTTP OK response.
     */
    @RequestMapping(method = GET, path = "/customer/{id}")
    public ResponseEntity<String> getCustomer(@PathVariable("id") final int id) {
        LOGGER.info("Get customer #{}.", id);
        return ResponseEntity.ok("");
    }

    /**
     * Handle DELETE requests to /customer endpoint.
     *
     * @return an HTTP OK response.
     */
    @RequestMapping(method = DELETE, path = "/customer/{id}")
    public ResponseEntity<String> deleteCustomer(@PathVariable("id") final int id) {
        LOGGER.info("Delete customer #{}.", id);
        return ResponseEntity.ok("");
    }

}

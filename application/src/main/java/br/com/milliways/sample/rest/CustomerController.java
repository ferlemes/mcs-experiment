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

import br.com.milliways.sample.bean.CustomerBean;
import br.com.milliways.sample.entity.Customer;
import br.com.milliways.sample.repository.CustomerRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;

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
     * The customer repository instance that will be used to access the database.
     */
    @Autowired
    private CustomerRepository customerRepository;

    /**
     * Handle POST requests to /customer endpoint.
     *
     * @return an HTTP OK response.
     */
    @RequestMapping(method = POST, path = "/customer")
    public ResponseEntity<CustomerBean> addCustomer(@RequestBody CustomerBean customerBean) {

        LOGGER.info("Adding new customer with name {}", customerBean.getName());

        // Save customer to db
        final Customer customer = new Customer();
        customer.setName(customerBean.getName());
        final Customer savedCustomer = customerRepository.save(customer);

        // Create the response object
        final CustomerBean responseCustomer = new CustomerBean();
        responseCustomer.setId(savedCustomer.getId());
        responseCustomer.setName(savedCustomer.getName());

        return ResponseEntity.status(HttpStatus.CREATED).body(responseCustomer);
    }

    /**
     * Handle GET requests to /customer endpoint.
     *
     * @return an HTTP OK response.
     */
    @RequestMapping(method = GET, path = "/customer/{id}")
    public ResponseEntity<CustomerBean> getCustomer(@PathVariable("id") final int id) {

        LOGGER.info("Get customer #{}.", id);

        // Get the customer record
        final Optional<Customer> customer = customerRepository.findById(id);

        if (customer.isPresent()) {

            // Create the response object
            final CustomerBean responseCustomer = new CustomerBean();
            responseCustomer.setId(customer.get().getId());
            responseCustomer.setName(customer.get().getName());

            return ResponseEntity.status(HttpStatus.OK).body(responseCustomer);

        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }

    }

    /**
     * Handle DELETE requests to /customer endpoint.
     *
     * @return an HTTP OK response.
     */
    @RequestMapping(method = DELETE, path = "/customer/{id}")
    public ResponseEntity<String> deleteCustomer(@PathVariable("id") final int id) {

        LOGGER.info("Delete customer #{}.", id);

        // Get the customer record just to check it if exists.
        final Optional<Customer> customer = customerRepository.findById(id);

        if (customer.isPresent()) {

            // Remove the customer from db
            customerRepository.deleteById(id);

            return ResponseEntity.status(HttpStatus.NO_CONTENT).build();

        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }

    }

}

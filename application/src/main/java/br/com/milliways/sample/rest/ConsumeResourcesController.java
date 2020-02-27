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

import static org.springframework.web.bind.annotation.RequestMethod.GET;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * This rest controller handles the requests to consume computational resources.
 */
@RestController
public class ConsumeResourcesController {

    /**
     * The logger for this controller.
     */
    private static final Logger LOGGER = LoggerFactory.getLogger(ConsumeResourcesController.class);

    /**
     * Handle GET requests to /consume/cpu endpoint.
     *
     * @return an HTTP OK response with the 40th element of the fibonacci series.
     */
    @RequestMapping(method = GET, path = "/consume/cpu")
    public ResponseEntity<String> getConsumeCPU() {
        LOGGER.info(Thread.currentThread() + " consumeCPU() started.");
        final Integer fib = consumeCPU();
        LOGGER.info(Thread.currentThread() + " consumeCPU() finished.");
        return ResponseEntity.ok("fib(40) is " + fib);
    }

    /**
     * Handle GET requests to /consume/memory endpoint.
     *
     * @return an HTTP OK response with a random integer.
     */
    @RequestMapping(method = GET, path = "/consume/memory")
    public ResponseEntity<String> getConsumeMemory() {
        LOGGER.info(Thread.currentThread() + " consumeMemory() started.");
        final Integer finalAnswer = consumeMemory();
        LOGGER.info(Thread.currentThread() + " consumeMemory() finished.");
        return ResponseEntity.ok("A random integer: " + finalAnswer);
    }

    /**
     * Handle GET requests to /consume/memoryAndCPU endpoint.
     *
     * @return an HTTP OK response with a random integer.
     */
    @RequestMapping(method = GET, path = "/consume/memoryAndCPU")
    public ResponseEntity<String> getConsumeMemoryAndCPU() {
        LOGGER.info(Thread.currentThread() + " consumeMemoryAndCPU() started.");
        final Integer randomLastNumber = consumeMemoryAndCPU();
        LOGGER.info(Thread.currentThread() + " consumeMemoryAndCPU() finished.");
        return ResponseEntity.ok("Another random integer: " + randomLastNumber);
    }

    /**
     * Calculate the 40th element of the fibonacci series.
     *
     * @return the 40th element of the fibonacci series.
     */
    private Integer consumeCPU() {
        return fib(40);
    }

    /**
     * Calculate the n-th element of the fibonacci series.
     *
     * @param n the n-th.
     * @return the value of the n-th element of the fibonacci series.
     */
    private int fib(final int n) {
        if (n == 0) {
            return 0;
        } else if (n == 1) {
            return 1;
        } else {
            return fib(n - 1) + fib(n - 2);
        }
    }

    /**
     * Consume memory by populating a list of a million integers.
     *
     * @return a random number from the array.
     */
    private Integer consumeMemory() {
        List<Integer> anArray = new ArrayList<>(1000000);
        for (int index = 0; index < 1000000; index++) {
            anArray.add((int) (Math.random() * Integer.MAX_VALUE));
        }
        return anArray.get((int) Math.floor(Math.random() * 1000000));
    }

    /**
     * Consume memory by populating a list of a million integers
     * and sort this array to consume CPU.
     *
     * @return the last integer from the list.
     */
    private Integer consumeMemoryAndCPU() {
        List<Integer> anArray = new ArrayList<>(1000000);
        for (int index = 0; index < 1000000; index++) {
            anArray.add((int) (Math.random() * Integer.MAX_VALUE));
        }
        Collections.sort(anArray);
        return anArray.get(anArray.size() - 1);
    }

}

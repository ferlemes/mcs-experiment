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

@RestController
public class SampleController {

    private static final Logger LOGGER = LoggerFactory.getLogger(SampleController.class);

    @RequestMapping(method = GET, path = "/health")
    public ResponseEntity<String> getHealth() {
        LOGGER.info("Health check invoked.");
        return ResponseEntity.ok("");
    }

    @RequestMapping(method = GET, path = "/consumeCPU")
    public ResponseEntity<String> getConsumeCPU() {
        LOGGER.debug(Thread.currentThread() + " consumeCPU() started.");
        final Integer fib = consumeCPU();
        LOGGER.debug(Thread.currentThread() + " consumeCPU() finished.");
        return ResponseEntity.ok("fib(40) is " + fib);
    }

    @RequestMapping(method = GET, path = "/consumeMemory")
    public ResponseEntity<String> getConsumeMemory() {
        LOGGER.debug(Thread.currentThread() + " consumeMemory() started.");
        final Integer finalAnswer = consumeMemory();
        LOGGER.debug(Thread.currentThread() + " consumeMemory() finished.");
        return ResponseEntity.ok("Item at 42th position was " + finalAnswer);
    }

    @RequestMapping(method = GET, path = "/consumeMemoryAndCPU")
    public ResponseEntity<String> getConsumeMemoryAndCPU() {
        LOGGER.debug(Thread.currentThread() + " consumeMemoryAndCPU() started.");
        final Integer randomLastNumber = consumeMemoryAndCPU();
        LOGGER.debug(Thread.currentThread() + " consumeMemoryAndCPU() finished.");
        return ResponseEntity.ok("Last item of the array was " + randomLastNumber);
    }

    private Integer consumeCPU() {
        return fib(40);
    }

    private int fib(final int n) {
        if (n == 0) {
            return 0;
        } else if (n == 1) {
            return 1;
        } else {
            return fib(n - 1) + fib(n - 2);
        }
    }

    private Integer consumeMemory() {
        List<Integer> anArray = new ArrayList<Integer>();
        for (int index = 0; index < 1000000; index++) {
            anArray.add((int) (Math.random() * Integer.MAX_VALUE));
        }
        return anArray.get(42);
    }

    private Integer consumeMemoryAndCPU() {
        List<Integer> anArray = new ArrayList<>();
        for (int index = 0; index < 1000000; index++) {
            anArray.add((int) (Math.random() * Integer.MAX_VALUE));
        }
        Collections.sort(anArray);
        return anArray.get(anArray.size() - 1);
    }

}

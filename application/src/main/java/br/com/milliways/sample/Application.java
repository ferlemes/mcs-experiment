package br.com.milliways.sample;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.stereotype.Controller;

@Controller
@EnableAutoConfiguration
@ComponentScan
public class Application {

    public static void main(final String... arguments) {
        SpringApplication.run(Application.class, arguments);
    }

}

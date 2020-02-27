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

package br.com.milliways.sample;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.stereotype.Controller;

/**
 * This is just the main class to start the web application.
 */
@Controller
@EnableAutoConfiguration
@ComponentScan
public class Application {

    /**
     * This is the main method of the Spring application.
     *
     * @param arguments arguments from the command line.
     */
    public static void main(final String... arguments) {
        SpringApplication.run(Application.class, arguments);
    }

}
